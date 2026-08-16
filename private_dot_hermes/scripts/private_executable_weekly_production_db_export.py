#!/usr/bin/env python3
"""Follow the authoritative production Temporal RDS export into a local snapshot.

The script is designed for a weekly Hermes no-agent cron job. It never starts or
mutates an RDS export. It keeps the current local snapshot until a fresh,
warning-free Temporal export has downloaded with S3
checksum validation and passed exact key grammar, metadata, size, and local
SHA-256 manifest checks, then swaps the directories on the same filesystem.
Successful scheduled runs are silent; failures exit non-zero while preserving
a validated snapshot.
"""

from __future__ import annotations

import argparse
import ctypes
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import NamedTuple

TASK_PREFIX = "transformity-no-audit-scraper-"
TASK_ID_PATTERN = re.compile(rf"{re.escape(TASK_PREFIX)}[0-9a-f]{{30}}")
ACTIVE_PHASES = {
    "selected",
    "complete",
    "downloading",
    "downloaded",
    "installing",
}

AT_FDCWD = -100
RENAME_EXCHANGE = 2


def validate_task_id(task_id: object) -> str:
    if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
        raise RuntimeError(f"unsafe RDS export task identifier in state: {task_id!r}")
    return task_id


def atomic_exchange(left: Path, right: Path) -> None:
    """Atomically exchange two existing paths without removing either name."""
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError as exc:
        raise RuntimeError(
            "renameat2 is unavailable; refusing a non-atomic swap"
        ) from exc
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        AT_FDCWD,
        os.fsencode(left),
        AT_FDCWD,
        os.fsencode(right),
        RENAME_EXCHANGE,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            f"atomic directory exchange failed: {os.strerror(error_number)}",
            f"{left} <-> {right}",
        )


def fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class Settings:
    def __init__(
        self,
        *,
        target: Path = Path("/root/dev/production_db"),
        state_file: Path = Path("/root/.hermes/state/weekly_production_db_export.json"),
        lock_file: Path = Path("/root/.hermes/state/weekly_production_db_export.lock"),
        account_id: str = "928004597368",
        region: str = "us-east-1",
        profile: str = "production",
        caller_arn: str | None = None,
        source_arn: str = "arn:aws:rds:us-east-1:928004597368:cluster:transformity-production",
        export_only: tuple[str, ...] = ("postgres.reference", "postgres.public"),
        s3_bucket: str = "transformity-rds-export-backups20260728044104962600000001",
        iam_role_arn: str = "arn:aws:iam::928004597368:role/service-role/rds-export",
        kms_key_arn: str = "arn:aws:kms:us-east-1:928004597368:key/af762111-98be-4740-8cc0-04e440913e0f",
        max_export_age: timedelta = timedelta(hours=48),
        sync_timeout_seconds: int = 15 * 60,
        free_space_headroom_bytes: int = 1024**3,
    ):
        self.target = target
        self.state_file = state_file
        self.lock_file = lock_file
        self.account_id = account_id
        self.region = region
        self.profile = profile
        self.caller_arn = caller_arn or (
            f"arn:aws:sts::{account_id}:assumed-role/"
            "HermesAgentReadOnly/hermes-agent-production"
        )
        self.source_arn = source_arn
        self.export_only = export_only
        self.s3_bucket = s3_bucket
        self.iam_role_arn = iam_role_arn
        self.kms_key_arn = kms_key_arn
        self.max_export_age = max_export_age
        self.sync_timeout_seconds = sync_timeout_seconds
        self.free_space_headroom_bytes = free_space_headroom_bytes

    def staging_path(self, task_id: str) -> Path:
        validate_task_id(task_id)
        return self.target.parent / f".{self.target.name}.{task_id}.staging"

    def backup_path(self, task_id: str) -> Path:
        validate_task_id(task_id)
        return self.target.parent / f".{self.target.name}.{task_id}.previous"


class RefreshResult(NamedTuple):
    changed: bool
    task_id: str
    object_count: int = 0
    total_bytes: int = 0


class Inventory(NamedTuple):
    objects: dict[str, int]
    object_count: int
    total_bytes: int


class ExportCandidate(NamedTuple):
    task_id: str
    timestamp: datetime
    task: dict


class CandidatePlan(NamedTuple):
    candidate: ExportCandidate
    resume: bool
    abandoned_task_id: str = ""


class InstallRecoveryPlan(NamedTuple):
    task_id: str
    action: str


class TrustedTarget(NamedTuple):
    candidate: ExportCandidate
    evidence: dict


class AWSCommandError(RuntimeError):
    pass


class PermanentExportError(RuntimeError):
    pass


class AWSClient:
    def __init__(self, settings: Settings, binary: str | None = None):
        self.settings = settings
        self.binary = binary or resolve_aws_binary()
        self.env = clean_aws_environment(settings)

    def _command(self, *args: str) -> list[str]:
        return [
            self.binary,
            "--profile",
            self.settings.profile,
            "--region",
            self.settings.region,
            "--no-cli-pager",
            *args,
        ]

    def _run(
        self,
        *args: str,
        timeout: int,
        json_output: bool = True,
    ) -> dict:
        self._validate_read_only_command(args)
        command = self._command(*args)
        if json_output:
            command.extend(["--output", "json"])
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self.env,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            raise AWSCommandError(
                f"AWS command timed out after {timeout}s: {' '.join(args[:2])}"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown AWS CLI error").strip()
            raise AWSCommandError(
                f"AWS command failed ({' '.join(args[:2])}): {detail[:2000]}"
            )
        if not json_output:
            return {}
        try:
            value = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise AWSCommandError(
                f"AWS command returned invalid JSON: {' '.join(args[:2])}"
            ) from exc
        if not isinstance(value, dict):
            raise AWSCommandError(
                f"AWS command returned unexpected JSON: {' '.join(args[:2])}"
            )
        return value

    def _validate_read_only_command(self, args: tuple[str, ...]) -> None:
        operation = args[:2]
        allowed = {
            ("sts", "get-caller-identity"),
            ("rds", "describe-export-tasks"),
            ("s3api", "list-objects-v2"),
            ("s3", "sync"),
            ("s3", "cp"),
        }
        if operation not in allowed:
            raise RuntimeError(
                f"AWS operation is not read-only allowlisted: {operation}"
            )
        if operation == ("s3", "sync"):
            expected_source = f"s3://{self.settings.s3_bucket}/"
            if (
                len(args) < 4
                or not args[2].startswith(expected_source)
                or args[3].startswith("s3://")
            ):
                raise RuntimeError(
                    "AWS S3 sync must copy from the pinned bucket to disk"
                )
        if operation == ("s3", "cp"):
            expected_source = f"s3://{self.settings.s3_bucket}/"
            if (
                len(args) < 4
                or not args[2].startswith(expected_source)
                or args[3] != "-"
            ):
                raise RuntimeError(
                    "AWS S3 cp must stream from the pinned bucket to stdout"
                )
            relative = args[2].removeprefix(expected_source)
            try:
                task_id, name = relative.split("/", maxsplit=1)
                validate_task_id(task_id)
            except (ValueError, RuntimeError) as exc:
                raise RuntimeError(
                    "AWS S3 cp source is not task-scoped metadata"
                ) from exc
            table_pattern = re.compile(
                rf"export_tables_info_{re.escape(task_id)}_from_[0-9]+_to_[0-9]+\.json"
            )
            if (
                name != f"export_info_{task_id}.json"
                and table_pattern.fullmatch(name) is None
            ):
                raise RuntimeError("AWS S3 cp source is not task-scoped metadata")

    def _run_text(self, *args: str, timeout: int) -> str:
        self._validate_read_only_command(args)
        try:
            result = subprocess.run(
                self._command(*args),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self.env,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            raise AWSCommandError(
                f"AWS command timed out after {timeout}s: {' '.join(args[:2])}"
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown AWS CLI error").strip()
            raise AWSCommandError(
                f"AWS command failed ({' '.join(args[:2])}): {detail[:2000]}"
            )
        return result.stdout

    def get_identity(self) -> dict:
        return self._run("sts", "get-caller-identity", timeout=60)

    def list_export_tasks(self) -> list[dict]:
        response = self._run(
            "rds",
            "describe-export-tasks",
            "--source-arn",
            self.settings.source_arn,
            timeout=120,
        )
        tasks = response.get("ExportTasks")
        if not isinstance(tasks, list):
            raise AWSCommandError(
                "RDS export task listing returned no ExportTasks list"
            )
        return tasks

    def describe_export(self, task_id: str) -> dict | None:
        try:
            response = self._run(
                "rds",
                "describe-export-tasks",
                "--export-task-identifier",
                task_id,
                timeout=120,
            )
        except AWSCommandError as exc:
            if "ExportTaskNotFound" in str(exc) or "not found" in str(exc).lower():
                return None
            raise
        tasks = response.get("ExportTasks", [])
        if not tasks:
            return None
        if len(tasks) != 1:
            raise AWSCommandError(
                f"expected one RDS export task for {task_id}, got {len(tasks)}"
            )
        return tasks[0]

    def list_export_objects(self, task_id: str) -> list[dict]:
        response = self._run(
            "s3api",
            "list-objects-v2",
            "--bucket",
            self.settings.s3_bucket,
            "--prefix",
            f"{task_id}/",
            timeout=180,
        )
        return response.get("Contents", [])

    def get_export_metadata(
        self,
        task_id: str,
        names: list[str],
    ) -> dict[str, object]:
        documents: dict[str, object] = {}
        for name in names:
            source = f"s3://{self.settings.s3_bucket}/{task_id}/{name}"
            value = self._run_text(
                "s3",
                "cp",
                source,
                "-",
                "--only-show-errors",
                timeout=120,
            )
            try:
                documents[name] = json.loads(value)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid remote export metadata: {name}") from exc
        return documents

    def sync_export(self, task_id: str, destination: Path) -> None:
        self._run(
            "s3",
            "sync",
            f"s3://{self.settings.s3_bucket}/{task_id}/",
            str(destination),
            "--delete",
            "--only-show-errors",
            "--no-progress",
            "--checksum-mode",
            "ENABLED",
            timeout=self.settings.sync_timeout_seconds,
            json_output=False,
        )


def resolve_aws_binary() -> str:
    candidate = Path("/root/.local/share/mise/installs/aws/2.36.19/.mise-bins/aws")
    try:
        resolved = candidate.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise RuntimeError(f"trusted AWS CLI is unavailable: {candidate}") from exc
    if (
        not resolved.is_file()
        or not os.access(resolved, os.X_OK)
        or metadata.st_uid != 0
        or metadata.st_mode & 0o022
    ):
        raise RuntimeError(f"trusted AWS CLI has unsafe ownership or mode: {resolved}")
    return str(candidate)


def clean_aws_environment(settings: Settings) -> dict[str, str]:
    # Build from an allowlist rather than trying to enumerate ambient credential,
    # proxy, endpoint, custom-CA, service-model, and provider selectors.
    return {
        "HOME": "/root",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "AWS_PROFILE": settings.profile,
        "AWS_CONFIG_FILE": "/root/.aws/config",
        "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
        "BOTO_CONFIG": "/dev/null",
        "AWS_REGION": settings.region,
        "AWS_DEFAULT_REGION": settings.region,
        "AWS_PAGER": "",
        "AWS_EC2_METADATA_DISABLED": "true",
        "PATH": "/usr/bin:/bin",
    }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read export state {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TypeError(f"export state must be a JSON object: {path}")
    return value


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(state, indent=2, sort_keys=True) + "\n"
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def updated_state(
    state: dict, clock: Callable[[], datetime], **changes: object
) -> dict:
    result = dict(state)
    result.update(changes)
    result["version"] = 2
    result["updated_at"] = clock().astimezone(timezone.utc).isoformat()
    return result


def save_rejected_state(
    settings: Settings,
    state: dict,
    task_id: str,
    clock: Callable[[], datetime],
    error: Exception,
) -> None:
    save_state(
        settings.state_file,
        updated_state(
            state,
            clock,
            phase="rejected",
            task_id=task_id,
            rejection_reason=str(error)[:2000],
        ),
    )


def verify_identity(settings: Settings, identity: dict) -> None:
    account = str(identity.get("Account", ""))
    if account != settings.account_id:
        raise RuntimeError(
            f"expected AWS account {settings.account_id}, got {account or 'unknown'}"
        )
    arn = str(identity.get("Arn", ""))
    if arn != settings.caller_arn:
        raise RuntimeError(
            f"expected AWS caller {settings.caller_arn}, got {arn or 'unknown'}"
        )


def task_timestamp(task_id: str, task: dict) -> datetime:
    for field in ("TaskEndTime", "TaskStartTime"):
        timestamp = parse_timestamp(task.get(field))
        if timestamp is not None:
            return timestamp
    raise RuntimeError(f"RDS export {task_id} has no valid completion/start timestamp")


def state_provenance(settings: Settings, candidate: ExportCandidate) -> dict:
    return {
        "task_id": candidate.task_id,
        "task_timestamp": candidate.timestamp.isoformat(),
        "source_arn": settings.source_arn,
        "s3_bucket": settings.s3_bucket,
        "export_only": list(settings.export_only),
        "iam_role_arn": settings.iam_role_arn,
        "kms_key_arn": settings.kms_key_arn,
    }


def state_has_static_provenance(settings: Settings, state: dict) -> bool:
    expected = {
        "source_arn": settings.source_arn,
        "s3_bucket": settings.s3_bucket,
        "export_only": list(settings.export_only),
        "iam_role_arn": settings.iam_role_arn,
        "kms_key_arn": settings.kms_key_arn,
    }
    return state.get("version") == 2 and all(
        state.get(key) == value for key, value in expected.items()
    )


def state_has_provenance(
    settings: Settings, state: dict, candidate: ExportCandidate
) -> bool:
    return (
        state_has_static_provenance(settings, state)
        and state.get("task_id") == candidate.task_id
        and parse_timestamp(state.get("task_timestamp")) == candidate.timestamp
    )


def validate_candidate_freshness(
    settings: Settings, candidate: ExportCandidate, now: datetime
) -> None:
    now = now.astimezone(timezone.utc)
    age = now - candidate.timestamp
    if age < timedelta(0):
        raise RuntimeError(
            f"latest RDS export {candidate.task_id} has a future task timestamp"
        )
    if age > settings.max_export_age:
        raise RuntimeError(
            f"latest RDS export {candidate.task_id} is older than "
            f"{settings.max_export_age.total_seconds() / 3600:g} hours"
        )


def validate_completed_task(settings: Settings, task_id: str, task: dict) -> None:
    expected = {
        "ExportTaskIdentifier": task_id,
        "SourceArn": settings.source_arn,
        "S3Bucket": settings.s3_bucket,
        "IamRoleArn": settings.iam_role_arn,
        "KmsKeyId": settings.kms_key_arn,
    }
    for key, value in expected.items():
        if task.get(key) != value:
            raise RuntimeError(
                f"RDS export {task_id} has unexpected {key}: {task.get(key)!r}"
            )
    export_only = task.get("ExportOnly")
    if (
        not isinstance(export_only, list)
        or not all(isinstance(scope, str) for scope in export_only)
        or len(export_only) != len(settings.export_only)
        or set(export_only) != set(settings.export_only)
    ):
        raise RuntimeError(
            f"RDS export {task_id} has unexpected ExportOnly: {task.get('ExportOnly')!r}"
        )
    if task.get("S3Prefix") != "":
        raise RuntimeError(
            f"RDS export {task_id} has unexpected S3Prefix: {task.get('S3Prefix')!r}"
        )
    if task.get("Status") != "COMPLETE":
        raise RuntimeError(
            f"RDS export {task_id} is not complete: {task.get('Status')!r}"
        )
    progress = task.get("PercentProgress")
    if isinstance(progress, bool) or not isinstance(progress, int) or progress != 100:
        raise RuntimeError(
            f"RDS export {task_id} has invalid PercentProgress: {progress!r}"
        )
    start = parse_timestamp(task.get("TaskStartTime"))
    end_value = task.get("TaskEndTime")
    end = start if end_value is None else parse_timestamp(end_value)
    if start is None or end is None or start > end:
        raise RuntimeError(f"RDS export {task_id} has invalid task timestamps")
    total = task.get("TotalExtractedDataInGB")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise RuntimeError(
            f"RDS export {task_id} has invalid TotalExtractedDataInGB: {total!r}"
        )
    warning = task.get("WarningMessage")
    if warning not in (None, ""):
        raise RuntimeError(f"RDS export {task_id} completed with a warning: {warning}")


def select_latest_completed_export(
    settings: Settings,
    tasks: list[dict],
    now: datetime,
) -> ExportCandidate:
    """Select and validate the newest completed authoritative Temporal export."""
    candidates: list[ExportCandidate] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise TypeError(f"invalid RDS export task listing entry: {task!r}")
        task_id = task.get("ExportTaskIdentifier")
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            continue
        if task.get("Status") != "COMPLETE":
            continue
        if task.get("SourceArn") != settings.source_arn:
            raise RuntimeError(
                f"RDS source-scoped listing returned unexpected SourceArn for {task_id}"
            )
        candidates.append(ExportCandidate(task_id, task_timestamp(task_id, task), task))
    if not candidates:
        raise RuntimeError("no qualifying completed Temporal RDS export exists")
    newest_timestamp = max(candidate.timestamp for candidate in candidates)
    newest = [
        candidate for candidate in candidates if candidate.timestamp == newest_timestamp
    ]
    newest_ids = {candidate.task_id for candidate in newest}
    if len(newest_ids) != 1:
        raise RuntimeError(
            "multiple completed Temporal RDS exports share the newest timestamp: "
            + ", ".join(sorted(newest_ids))
        )
    selected = newest[0]
    validate_completed_task(settings, selected.task_id, selected.task)
    validate_candidate_freshness(settings, selected, now)
    return selected


def is_allowed_export_data_key(relative: str, export_only: tuple[str, ...]) -> bool:
    parts = PurePosixPath(relative).parts
    if len(parts) != 4:
        return False
    database, qualified_table, partition, filename = parts
    if re.fullmatch(r"[0-9]+", partition) is None:
        return False
    if (
        filename != "_SUCCESS"
        and re.fullmatch(r"part-[A-Za-z0-9._-]+\.parquet", filename) is None
    ):
        return False
    for scope in export_only:
        expected_database, schema = scope.split(".", maxsplit=1)
        table_prefix = f"{schema}."
        if database != expected_database or not qualified_table.startswith(
            table_prefix
        ):
            continue
        table = qualified_table.removeprefix(table_prefix)
        return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", table) is not None
    return False


def validate_inventory_names(
    task_id: str,
    names: set[str] | dict[str, int],
    export_only: tuple[str, ...],
) -> None:
    expected_info = f"export_info_{task_id}.json"
    table_info_prefix = f"export_tables_info_{task_id}_"
    table_info_pattern = re.compile(
        rf"{re.escape(table_info_prefix)}from_[0-9]+_to_[0-9]+\.json"
    )
    allowed_data_prefixes = tuple(
        f"{scope.split('.', maxsplit=1)[0]}/{scope.split('.', maxsplit=1)[1]}."
        for scope in export_only
    )
    for relative in names:
        parts = PurePosixPath(relative).parts
        if not relative or relative.startswith("/") or ".." in parts:
            raise RuntimeError(f"unsafe export object key for {task_id}: {relative!r}")
        is_table_metadata = table_info_pattern.fullmatch(relative) is not None
        if relative.startswith(table_info_prefix) and not is_table_metadata:
            raise RuntimeError(f"unexpected table metadata key: {relative}")
        is_metadata = relative == expected_info or is_table_metadata
        if not is_metadata and not relative.startswith(allowed_data_prefixes):
            raise RuntimeError(
                f"S3 object is outside requested export scopes: {relative}"
            )
        if not is_metadata and not is_allowed_export_data_key(relative, export_only):
            raise RuntimeError(f"unexpected export data key: {relative}")
    if expected_info not in names:
        raise RuntimeError(f"RDS export {task_id} is missing {expected_info}")
    if not any(table_info_pattern.fullmatch(name) is not None for name in names):
        raise RuntimeError(f"RDS export {task_id} has no table metadata")


def build_inventory(
    task_id: str,
    raw_objects: list[dict],
    export_only: tuple[str, ...],
) -> Inventory:
    prefix = f"{task_id}/"
    objects: dict[str, int] = {}
    for item in raw_objects:
        if not isinstance(item, dict):
            raise RuntimeError(  # noqa: TRY004 - malformed external AWS response
                f"invalid S3 inventory entry for {task_id}: {item!r}"
            )
        key = item.get("Key")
        size = item.get("Size")
        if not isinstance(key, str) or not key.startswith(prefix):
            raise RuntimeError(f"unexpected S3 object key for {task_id}: {key!r}")
        relative = key.removeprefix(prefix)
        if not isinstance(size, int) or size < 0:
            raise RuntimeError(f"unexpected S3 object size for {key}: {size!r}")
        checksum_algorithms = item.get("ChecksumAlgorithm")
        if (
            not isinstance(checksum_algorithms, list)
            or not checksum_algorithms
            or not all(
                isinstance(algorithm, str) and algorithm
                for algorithm in checksum_algorithms
            )
        ):
            raise RuntimeError(f"S3 object does not expose an S3 checksum: {key}")
        if relative in objects:
            raise RuntimeError(f"duplicate S3 object key for {task_id}: {relative}")
        objects[relative] = size

    validate_inventory_names(task_id, objects, export_only)
    return Inventory(objects, len(objects), sum(objects.values()))


def local_inventory(directory: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for root, directories, filenames in os.walk(directory, followlinks=False):
        root_path = Path(root)
        for name in directories:
            path = root_path / name
            if path.is_symlink():
                raise RuntimeError(f"download contains a symlinked directory: {path}")
        for name in filenames:
            path = root_path / name
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"download contains a non-regular file: {path}")
            relative = path.relative_to(directory).as_posix()
            result[relative] = path.stat().st_size
    return result


def sha256_inventory(directory: Path, names: dict[str, int]) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for relative in sorted(names):
        digest = hashlib.sha256()
        path = directory / relative
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                digest.update(chunk)
        checksums[relative] = digest.hexdigest()
    return checksums


def validate_sha256_manifest(value: object, inventory: Inventory) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(inventory.objects):
        raise RuntimeError("missing or incomplete local SHA-256 manifest")
    manifest: dict[str, str] = {}
    for name, checksum in value.items():
        if not isinstance(name, str) or not isinstance(checksum, str):
            raise RuntimeError(  # noqa: TRY004 - malformed persisted manifest
                "invalid local SHA-256 manifest"
            )
        if re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            raise RuntimeError(f"invalid SHA-256 checksum for {name}")
        manifest[name] = checksum
    return manifest


def discard_untrusted_reusable_files(
    directory: Path,
    local: dict[str, int],
    inventory: Inventory,
    expected_sha256: dict[str, str] | None,
) -> dict[str, int]:
    """Force transfer unless a same-size staging file matches trusted state."""
    reusable = {
        name: size
        for name, size in local.items()
        if inventory.objects.get(name) == size
    }
    if not reusable:
        return local
    discard = list(reusable)
    if expected_sha256 is not None:
        actual = sha256_inventory(directory, reusable)
        discard = [name for name in reusable if actual[name] != expected_sha256[name]]
    for name in discard:
        (directory / name).unlink()
        local.pop(name)
    return local


def validate_table_metadata_documents(
    documents: dict[str, object],
    task_id: str,
    export_only: tuple[str, ...],
    object_names: set[str] | dict[str, int],
) -> None:
    table_info_prefix = f"export_tables_info_{task_id}_"
    table_documents = sorted(
        (name, document)
        for name, document in documents.items()
        if name.startswith(table_info_prefix)
    )
    seen_targets: set[str] = set()
    incomplete: list[str] = []
    for name, document in table_documents:
        if not isinstance(document, dict):
            raise RuntimeError(  # noqa: TRY004 - malformed external export metadata
                f"invalid downloaded table metadata object: {name}"
            )
        entries = document.get("perTableStatus")
        if not isinstance(entries, list) or not entries:
            raise RuntimeError(
                f"downloaded table metadata has no table statuses: {name}"
            )
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("target"), str):
                raise RuntimeError(  # noqa: TRY004 - malformed external export metadata
                    f"invalid table status in downloaded metadata: {name}"
                )
            target = entry["target"]
            target_parts = target.split(".")
            scope = ".".join(target_parts[:2])
            if (
                len(target_parts) != 3
                or scope not in export_only
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", target_parts[2]) is None
            ):
                raise RuntimeError(
                    f"downloaded table target outside export scopes: {target}"
                )
            if target in seen_targets:
                raise RuntimeError(
                    f"duplicate table status in downloaded metadata: {target}"
                )
            seen_targets.add(target)
            if entry.get("status") != "COMPLETE":
                incomplete.append(f"{target}={entry.get('status')!r}")
    if incomplete:
        raise RuntimeError(
            "downloaded table metadata is incomplete: " + ", ".join(incomplete[:10])
        )
    missing_scopes = [
        scope
        for scope in export_only
        if not any(target.startswith(f"{scope}.") for target in seen_targets)
    ]
    if missing_scopes:
        raise RuntimeError(
            f"downloaded table metadata is missing export scopes: {missing_scopes}"
        )

    data_partitions: dict[tuple[str, str], set[str]] = {}
    for name in object_names:
        parts = PurePosixPath(name).parts
        if len(parts) != 4:
            continue
        database, qualified_table, partition, filename = parts
        target = f"{database}.{qualified_table}"
        if target not in seen_targets:
            raise RuntimeError(
                f"export data table {target} has no exact table metadata"
            )
        data_partitions.setdefault((target, partition), set()).add(filename)
    data_targets = {target for target, _partition in data_partitions}
    missing_data = sorted(seen_targets - data_targets)
    if missing_data:
        raise RuntimeError(
            "table metadata target has no export data or _SUCCESS: "
            + ", ".join(missing_data[:10])
        )
    missing_success = sorted(
        f"{target}/{partition}"
        for (target, partition), filenames in data_partitions.items()
        if "_SUCCESS" not in filenames
    )
    if missing_success:
        raise RuntimeError(
            "export data partitions are missing _SUCCESS: "
            + ", ".join(missing_success[:10])
        )


def validate_export_metadata_documents(
    documents: dict[str, object],
    task_id: str,
    settings: Settings,
    object_names: set[str] | dict[str, int],
    candidate_task: dict | None = None,
    expected_task_timestamp: datetime | None = None,
) -> None:
    info_name = f"export_info_{task_id}.json"
    info = documents.get(info_name)
    if not isinstance(info, dict):
        raise PermanentExportError(
            f"downloaded export metadata is not an object: {info_name}"
        )
    if info.get("exportTaskIdentifier") != task_id or info.get("status") != "COMPLETE":
        raise PermanentExportError(
            f"downloaded export metadata does not confirm {task_id}"
        )
    export_only = info.get("exportOnly")
    expected_export_only = set(settings.export_only)
    if (
        not isinstance(export_only, list)
        or not all(isinstance(scope, str) for scope in export_only)
        or len(export_only) != len(expected_export_only)
        or set(export_only) != expected_export_only
    ):
        raise PermanentExportError("downloaded export metadata has wrong export scopes")
    progress = info.get("percentProgress")
    if isinstance(progress, bool) or not isinstance(progress, int) or progress != 100:
        raise PermanentExportError(
            "downloaded export metadata has wrong percentProgress"
        )
    start = parse_timestamp(info.get("taskStartTime"))
    end = parse_timestamp(info.get("taskEndTime"))
    if start is None or end is None or start > end:
        raise PermanentExportError("downloaded export metadata has invalid task times")
    total = info.get("totalExportedDataInGB")
    if (
        isinstance(total, bool)
        or not isinstance(total, (int, float))
        or not math.isfinite(total)
        or total < 0
    ):
        raise PermanentExportError(
            "downloaded export metadata has invalid totalExportedDataInGB"
        )
    expected = {
        "sourceArn": settings.source_arn,
        "s3Bucket": settings.s3_bucket,
        "s3Prefix": "",
        "exportedFilesPath": task_id,
        "iamRoleArn": settings.iam_role_arn,
        "kmsKeyId": settings.kms_key_arn,
    }
    for field, value in expected.items():
        if info.get(field) != value:
            raise PermanentExportError(f"downloaded export metadata has wrong {field}")
    if candidate_task is not None:
        expected_start = parse_timestamp(candidate_task.get("TaskStartTime"))
        task_end_value = candidate_task.get("TaskEndTime")
        expected_end = (
            expected_start
            if task_end_value is None
            else parse_timestamp(task_end_value)
        )
        expected_total = candidate_task.get("TotalExtractedDataInGB")
        if start != expected_start:
            raise PermanentExportError(
                "downloaded export metadata has wrong taskStartTime"
            )
        if end != expected_end:
            raise PermanentExportError(
                "downloaded export metadata has wrong taskEndTime"
            )
        # RDS exposes this value as whole GiB while its sidecar records a
        # fractional value. Require the sidecar to stay in the selected bin.
        if (
            isinstance(expected_total, bool)
            or not isinstance(expected_total, int)
            or not expected_total <= total < expected_total + 1
        ):
            raise PermanentExportError(
                "downloaded export metadata has wrong totalExportedDataInGB"
            )
    if expected_task_timestamp is not None and end != expected_task_timestamp:
        raise PermanentExportError(
            "downloaded export metadata does not match the saved task timestamp"
        )
    try:
        validate_table_metadata_documents(
            documents, task_id, settings.export_only, object_names
        )
    except RuntimeError as exc:
        raise PermanentExportError(str(exc)) from exc


def validate_remote_export_metadata(
    aws,
    candidate: ExportCandidate,
    settings: Settings,
    inventory: Inventory,
) -> None:
    metadata_names = sorted(
        name
        for name in inventory.objects
        if name == f"export_info_{candidate.task_id}.json"
        or name.startswith(f"export_tables_info_{candidate.task_id}_")
    )
    documents = aws.get_export_metadata(candidate.task_id, metadata_names)
    validate_export_metadata_documents(
        documents,
        candidate.task_id,
        settings,
        inventory.objects,
        candidate.task,
    )


def read_export_metadata_documents(
    directory: Path,
    task_id: str,
    object_names: set[str] | dict[str, int],
) -> dict[str, object]:
    names = sorted(
        name
        for name in object_names
        if name == f"export_info_{task_id}.json"
        or name.startswith(f"export_tables_info_{task_id}_")
    )
    documents: dict[str, object] = {}
    for name in names:
        try:
            documents[name] = json.loads((directory / name).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise PermanentExportError(
                f"invalid downloaded export metadata: {name}"
            ) from exc
    return documents


def validate_download(
    directory: Path,
    task_id: str,
    inventory: Inventory,
    settings: Settings,
    expected_sha256: dict[str, str] | None = None,
    candidate_task: dict | None = None,
    expected_task_timestamp: datetime | None = None,
) -> None:
    if not directory.is_dir() or directory.is_symlink():
        raise RuntimeError(f"download directory is missing or unsafe: {directory}")
    local = local_inventory(directory)
    if local != inventory.objects:
        missing = sorted(set(inventory.objects) - set(local))[:5]
        extra = sorted(set(local) - set(inventory.objects))[:5]
        mismatched = sorted(
            key
            for key in set(local) & set(inventory.objects)
            if local[key] != inventory.objects[key]
        )[:5]
        raise RuntimeError(
            "download does not match S3 inventory "
            f"(missing={missing}, extra={extra}, size_mismatches={mismatched})"
        )
    documents = read_export_metadata_documents(directory, task_id, local)
    validate_export_metadata_documents(
        documents,
        task_id,
        settings,
        local,
        candidate_task,
        expected_task_timestamp,
    )
    if expected_sha256 is not None:
        manifest = validate_sha256_manifest(expected_sha256, inventory)
        actual = sha256_inventory(directory, inventory.objects)
        mismatches = [
            name for name in inventory.objects if actual[name] != manifest[name]
        ]
        if mismatches:
            raise RuntimeError(
                f"local SHA-256 mismatch for exported objects: {mismatches[:5]}"
            )


def validate_snapshot_directory(
    settings: Settings,
    directory: Path,
    task_id: str,
    manifest_value: object,
    expected_task_timestamp: datetime | None = None,
) -> Inventory:
    if not directory.is_dir() or directory.is_symlink():
        raise RuntimeError(f"download directory is missing or unsafe: {directory}")
    local = local_inventory(directory)
    validate_inventory_names(task_id, local, settings.export_only)
    inventory = Inventory(local, len(local), sum(local.values()))
    manifest = validate_sha256_manifest(manifest_value, inventory)
    validate_download(
        directory,
        task_id,
        inventory,
        settings,
        manifest,
        expected_task_timestamp=expected_task_timestamp,
    )
    return inventory


def validate_installed_snapshot(
    settings: Settings,
    task_id: str,
    manifest_value: object,
    expected_task_timestamp: datetime | None = None,
) -> Inventory:
    return validate_snapshot_directory(
        settings,
        settings.target,
        task_id,
        manifest_value,
        expected_task_timestamp,
    )


def check_download_space(
    directory: Path,
    inventory: Inventory,
    headroom_bytes: int,
) -> None:
    free = shutil.disk_usage(directory).free
    required = inventory.total_bytes + headroom_bytes
    if free < required:
        raise RuntimeError(
            f"not enough free disk for export: need {required / 1024**3:.2f} GiB, "
            f"have {free / 1024**3:.2f} GiB"
        )


def existing_directory(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    if not candidate.is_dir() or candidate.is_symlink():
        raise RuntimeError(f"download parent is missing or unsafe: {candidate}")
    return candidate


def ensure_download_space(settings: Settings, inventory: Inventory) -> None:
    settings.target.parent.mkdir(parents=True, exist_ok=True)
    check_download_space(
        settings.target.parent,
        inventory,
        settings.free_space_headroom_bytes,
    )


def check_dry_run_download_space(settings: Settings, inventory: Inventory) -> None:
    check_download_space(
        existing_directory(settings.target.parent),
        inventory,
        settings.free_space_headroom_bytes,
    )


def install_download(settings: Settings, task_id: str, staging: Path) -> None:
    target = settings.target
    backup = settings.backup_path(task_id)
    if staging.parent != target.parent or backup.parent != target.parent:
        raise RuntimeError("staging, target, and backup must share a parent filesystem")
    if backup.exists():
        raise RuntimeError(f"stale replacement backup requires inspection: {backup}")

    if target.exists():
        if not target.is_dir() or target.is_symlink():
            raise RuntimeError(f"refusing to replace unsafe target: {target}")
        # Linux renameat2(RENAME_EXCHANGE) guarantees the canonical target name
        # always resolves to either the old or new complete directory.
        atomic_exchange(target, staging)
        fsync_directory(target.parent)
        # The old target now occupies the staging name. Keep it as the backup
        # until the newly published target is validated and state is durable.
        staging.rename(backup)
        fsync_directory(target.parent)
    else:
        staging.rename(target)
        fsync_directory(target.parent)


def rollback_install(settings: Settings, task_id: str) -> None:
    target = settings.target
    staging = settings.staging_path(task_id)
    backup = settings.backup_path(task_id)
    if not target.exists():
        if backup.exists():
            backup.rename(target)
            fsync_directory(target.parent)
        return
    if backup.exists():
        if staging.exists():
            raise RuntimeError(
                f"cannot roll back with both staging and backup present: {task_id}"
            )
        atomic_exchange(target, backup)
        fsync_directory(target.parent)
        backup.rename(staging)
        fsync_directory(target.parent)
    elif staging.exists():
        atomic_exchange(target, staging)
        fsync_directory(target.parent)
    else:
        target.rename(staging)
        fsync_directory(target.parent)


def declared_export_task_id(directory: Path) -> str | None:
    """Return the one exact Temporal task declared by a snapshot directory."""
    if not directory.exists():
        return None
    if not directory.is_dir() or directory.is_symlink():
        raise RuntimeError(f"unsafe snapshot directory during planning: {directory}")
    declared: list[str] = []
    for path in directory.glob(f"export_info_{TASK_PREFIX}*.json"):
        match = re.fullmatch(r"export_info_(.+)\.json", path.name)
        if match is None or TASK_ID_PATTERN.fullmatch(match.group(1)) is None:
            continue
        task_id = match.group(1)
        try:
            info = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid snapshot export metadata: {path}") from exc
        if not isinstance(info, dict) or info.get("exportTaskIdentifier") != task_id:
            raise RuntimeError(f"mismatched snapshot export metadata: {path}")
        declared.append(task_id)
    if len(declared) > 1:
        raise RuntimeError(
            f"snapshot directory declares multiple export tasks: {directory}"
        )
    return declared[0] if declared else None


def describe_candidate(settings: Settings, aws, task_id: str) -> ExportCandidate:
    task = aws.describe_export(task_id)
    if task is None:
        raise RuntimeError(f"saved RDS export task no longer exists: {task_id}")
    validate_completed_task(settings, task_id, task)
    return ExportCandidate(task_id, task_timestamp(task_id, task), task)


def declared_snapshot_candidates(
    settings: Settings,
    aws,
    trusted_target: ExportCandidate | None = None,
) -> list[ExportCandidate]:
    task_id = declared_export_task_id(settings.target)
    if task_id is None:
        return []
    if trusted_target is not None and trusted_target.task_id == task_id:
        return [trusted_target]
    return [describe_candidate(settings, aws, task_id)]


def trusted_target_candidate(
    settings: Settings,
    state: dict,
    install_recovery: InstallRecoveryPlan | None,
) -> TrustedTarget | None:
    target_task_id = declared_export_task_id(settings.target)
    if target_task_id is None:
        return None
    nested = state.get("installed_target")
    sources: list[tuple[dict, bool]] = []
    if isinstance(nested, dict):
        sources.append((nested, True))
    sources.append((state, False))
    for evidence, independent in sources:
        if not state_has_static_provenance(settings, evidence):
            continue
        try:
            task_id = validate_task_id(evidence.get("task_id"))
        except RuntimeError:
            continue
        timestamp = parse_timestamp(evidence.get("task_timestamp"))
        if timestamp is None or task_id != target_task_id:
            continue
        if not independent:
            phase = state.get("phase")
            if phase != "installed" and not (
                phase == "installing"
                and install_recovery is not None
                and install_recovery.action == "published"
            ):
                continue
        try:
            validate_installed_snapshot(
                settings,
                task_id,
                evidence.get("sha256"),
                timestamp,
            )
        except RuntimeError:
            continue
        preserved = {
            key: evidence.get(key)
            for key in (
                "version",
                "task_id",
                "task_timestamp",
                "source_arn",
                "s3_bucket",
                "export_only",
                "iam_role_arn",
                "kms_key_arn",
                "sha256",
            )
        }
        return TrustedTarget(ExportCandidate(task_id, timestamp, {}), preserved)
    return None


def validate_no_downgrade(
    candidate: ExportCandidate,
    protected: list[ExportCandidate],
) -> None:
    newer = [item for item in protected if item.timestamp > candidate.timestamp]
    if newer:
        newest = max(newer, key=lambda item: item.timestamp)
        raise RuntimeError(
            "latest listed RDS export is older than the installed task; refusing a "
            f"downgrade from {newest.task_id} to {candidate.task_id}"
        )
    conflicts = [
        item
        for item in protected
        if item.timestamp == candidate.timestamp and item.task_id != candidate.task_id
    ]
    if conflicts:
        conflict = min(conflicts, key=lambda item: item.task_id)
        raise RuntimeError(
            "different RDS export tasks share a protected timestamp; refusing to "
            f"replace {conflict.task_id} with {candidate.task_id}"
        )


def plan_candidate(
    settings: Settings,
    aws,
    state: dict,
    now: datetime,
    trusted_target: ExportCandidate | None = None,
) -> CandidatePlan:
    """Choose resume versus replan with shared execution/dry-run safety gates."""
    phase = state.get("phase")
    protected = declared_snapshot_candidates(settings, aws, trusted_target)
    if phase == "installed" and state_has_static_provenance(settings, state):
        try:
            installed_task_id = validate_task_id(state.get("task_id"))
        except RuntimeError:
            pass
        else:
            installed_timestamp = parse_timestamp(state.get("task_timestamp"))
            if installed_timestamp is not None:
                protected.append(
                    ExportCandidate(installed_task_id, installed_timestamp, {})
                )

    abandoned_task_id = ""
    if phase in ACTIVE_PHASES:
        saved_timestamp = parse_timestamp(state.get("task_timestamp"))
        try:
            active_task_id = validate_task_id(state.get("task_id"))
        except RuntimeError:
            active_task_id = ""
        saved_is_stale = (
            saved_timestamp is not None
            and now - saved_timestamp > settings.max_export_age
        )

        if active_task_id and saved_timestamp is not None and saved_is_stale:
            abandoned_task_id = active_task_id
        elif active_task_id and saved_timestamp is not None:
            active = describe_candidate(settings, aws, active_task_id)
            if active.timestamp != saved_timestamp:
                raise RuntimeError(
                    f"saved timestamp for RDS export {active_task_id} no longer "
                    "matches AWS"
                )
            if not state_has_provenance(settings, state, active):
                abandoned_task_id = active_task_id
            else:
                try:
                    validate_candidate_freshness(settings, active, now)
                except RuntimeError:
                    abandoned_task_id = active_task_id
                else:
                    try:
                        validate_no_downgrade(active, protected)
                    except RuntimeError:
                        abandoned_task_id = active_task_id
                    else:
                        return CandidatePlan(active, True)
        elif active_task_id:
            abandoned_task_id = active_task_id

    candidate = select_latest_completed_export(settings, aws.list_export_tasks(), now)
    validate_no_downgrade(candidate, protected)
    return CandidatePlan(candidate, False, abandoned_task_id)


def resolve_installed_backup(
    settings: Settings,
    state: dict,
    *,
    remove: bool,
) -> bool:
    """Validate the installed snapshot before resolving its retained backup."""
    if state.get("phase") != "installed" or not state_has_static_provenance(
        settings, state
    ):
        return False
    task_id = validate_task_id(state.get("task_id"))
    backup = settings.backup_path(task_id)
    if not backup.exists() and not backup.is_symlink():
        return False
    if backup.is_symlink() or not backup.is_dir():
        raise RuntimeError(f"unsafe installed backup path: {backup}")
    try:
        validate_installed_snapshot(settings, task_id, state.get("sha256"))
    except RuntimeError as exc:
        raise RuntimeError(
            "cannot validate installed target before backup cleanup"
        ) from exc
    if remove:
        shutil.rmtree(backup)
        fsync_directory(settings.target.parent)
    return True


def validate_checkpoint_artifact_paths(settings: Settings, state: dict) -> None:
    phase = state.get("phase")
    if phase not in ACTIVE_PHASES and phase not in {"installed", "rejected"}:
        return
    try:
        task_id = validate_task_id(state.get("task_id"))
    except RuntimeError:
        return
    staging = settings.staging_path(task_id)
    backup = settings.backup_path(task_id)
    for label, path in (("staging", staging), ("backup", backup)):
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(f"refusing to use unsafe {label} path: {path}")
    if phase != "installing" and phase != "installed" and backup.exists():
        raise RuntimeError(f"stale replacement backup requires inspection: {backup}")


def abandon_active_checkpoint(settings: Settings, task_id: str) -> None:
    backup = settings.backup_path(task_id)
    if backup.exists() or backup.is_symlink():
        raise RuntimeError(
            f"cannot abandon active checkpoint with unresolved backup: {backup}"
        )
    staging = settings.staging_path(task_id)
    if staging.exists() or staging.is_symlink():
        if not staging.is_dir() or staging.is_symlink():
            raise RuntimeError(f"refusing to remove unsafe staging path: {staging}")
        shutil.rmtree(staging)
        fsync_directory(settings.target.parent)


def artifact_matches_active_manifest(
    settings: Settings,
    path: Path,
    task_id: str,
    manifest_value: object,
) -> bool:
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise RuntimeError(f"unsafe install-recovery artifact: {path}")
    if not path.exists():
        return False
    try:
        validate_snapshot_directory(settings, path, task_id, manifest_value)
    except RuntimeError:
        return False
    return True


def plan_interrupted_install(
    settings: Settings,
    state: dict,
) -> InstallRecoveryPlan | None:
    """Classify install artifacts without mutating them; shared by dry-run."""
    if state.get("phase") != "installing":
        return None
    if not state_has_static_provenance(settings, state):
        raise RuntimeError("installing checkpoint has untrusted static provenance")
    task_id = validate_task_id(state.get("task_id"))
    manifest = state.get("sha256")
    if not isinstance(manifest, dict) or not manifest:
        raise RuntimeError("installing checkpoint has no trusted SHA-256 manifest")

    target = settings.target
    staging = settings.staging_path(task_id)
    backup = settings.backup_path(task_id)
    staging_exists = staging.exists() or staging.is_symlink()
    backup_exists = backup.exists() or backup.is_symlink()
    if staging_exists and backup_exists:
        raise RuntimeError(
            f"ambiguous install recovery with staging and backup present: {task_id}"
        )

    target_is_active = artifact_matches_active_manifest(
        settings, target, task_id, manifest
    )
    staging_is_active = artifact_matches_active_manifest(
        settings, staging, task_id, manifest
    )
    backup_is_active = artifact_matches_active_manifest(
        settings, backup, task_id, manifest
    )

    if target_is_active:
        return InstallRecoveryPlan(task_id, "published")
    if staging_exists and staging_is_active:
        return InstallRecoveryPlan(task_id, "staged")
    if backup_exists and backup_is_active:
        return InstallRecoveryPlan(task_id, "backup_to_staging")
    raise RuntimeError(f"cannot locate a manifest-valid install artifact for {task_id}")


def apply_interrupted_install_plan(
    settings: Settings,
    plan: InstallRecoveryPlan | None,
) -> None:
    if plan is None or plan.action != "backup_to_staging":
        return
    backup = settings.backup_path(plan.task_id)
    staging = settings.staging_path(plan.task_id)
    backup.rename(staging)
    fsync_directory(settings.target.parent)


def cleanup_published_checkpoint_artifacts(
    settings: Settings,
    plan: InstallRecoveryPlan | None,
) -> None:
    if plan is None or plan.action != "published":
        return
    changed = False
    for path in (
        settings.staging_path(plan.task_id),
        settings.backup_path(plan.task_id),
    ):
        if path.exists():
            shutil.rmtree(path)
            changed = True
    if changed:
        fsync_directory(settings.target.parent)


def ensure_no_orphaned_target_backup(
    settings: Settings,
    state: dict,
    install_plan: InstallRecoveryPlan | None,
) -> None:
    """Fail closed when replayed state hides residue for the canonical target."""
    target_task_id = declared_export_task_id(settings.target)
    if target_task_id is None:
        return
    backup = settings.backup_path(target_task_id)
    if not backup.exists() and not backup.is_symlink():
        return
    trusted_installed = (
        state.get("phase") == "installed"
        and state_has_static_provenance(settings, state)
        and state.get("task_id") == target_task_id
        and isinstance(state.get("sha256"), dict)
    )
    trusted_installing = (
        state.get("phase") == "installing"
        and install_plan is not None
        and install_plan.task_id == target_task_id
    )
    if trusted_installed or trusted_installing:
        return
    raise RuntimeError(
        "canonical target has unresolved backup residue without trusted installed "
        f"evidence: {backup}"
    )


def finish_install(
    settings: Settings,
    task_id: str,
    inventory: Inventory,
    state: dict,
    clock: Callable[[], datetime],
    candidate_task: dict,
) -> dict:
    backup = settings.backup_path(task_id)
    staging = settings.staging_path(task_id)
    try:
        expected_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
        validate_download(
            settings.target,
            task_id,
            inventory,
            settings,
            expected_sha256,
            candidate_task,
        )
    except Exception:
        rollback_install(settings, task_id)
        raise
    # A crash immediately after the exchange leaves the old target under the
    # staging name. Normalize it to the backup name before recording success.
    if staging.exists():
        if backup.exists():
            raise RuntimeError(
                f"both staging and backup remain after publication: {task_id}"
            )
        if not staging.is_dir() or staging.is_symlink():
            raise RuntimeError(f"unsafe old snapshot after publication: {staging}")
        staging.rename(backup)
        fsync_directory(settings.target.parent)
    installed = updated_state(
        state,
        clock,
        phase="installed",
        task_id=task_id,
        installed_at=clock().astimezone(timezone.utc).isoformat(),
        object_count=inventory.object_count,
        total_bytes=inventory.total_bytes,
    )
    installed.pop("installed_target", None)
    save_state(settings.state_file, installed)
    # Once the new target is validated and persisted as installed, cleanup must
    # never roll it back to an old backup that may already be partially deleted.
    if backup.exists():
        shutil.rmtree(backup)
        fsync_directory(settings.target.parent)
    return installed


def refresh_once(
    settings: Settings,
    aws,
    *,
    force: bool = False,
    clock: Callable[[], datetime] = utc_now,
) -> RefreshResult:
    now = clock().astimezone(timezone.utc)
    verify_identity(settings, aws.get_identity())
    state = load_state(settings.state_file)
    phase = state.get("phase")
    validate_checkpoint_artifact_paths(settings, state)
    resolve_installed_backup(settings, state, remove=True)
    install_recovery = plan_interrupted_install(settings, state)
    ensure_no_orphaned_target_backup(settings, state, install_recovery)
    trusted_target_proof = trusted_target_candidate(settings, state, install_recovery)
    trusted_target = (
        trusted_target_proof.candidate if trusted_target_proof is not None else None
    )

    plan = plan_candidate(settings, aws, state, now, trusted_target)
    candidate = plan.candidate
    resume = plan.resume
    if not resume:
        if plan.abandoned_task_id:
            cleanup_published_checkpoint_artifacts(settings, install_recovery)
            apply_interrupted_install_plan(settings, install_recovery)
            abandon_active_checkpoint(settings, plan.abandoned_task_id)

        if (
            not force
            and phase == "installed"
            and trusted_target is not None
            and trusted_target.task_id == candidate.task_id
        ):
            installed_files = local_inventory(settings.target)
            return RefreshResult(
                False,
                candidate.task_id,
                len(installed_files),
                sum(installed_files.values()),
            )

        if (
            phase == "installed"
            and trusted_target is None
            and state_has_provenance(settings, state, candidate)
            and state.get("sha256") is not None
        ):
            try:
                inventory = validate_installed_snapshot(
                    settings, candidate.task_id, state.get("sha256")
                )
            except RuntimeError:
                # An untrusted or mismatched current target is migration input,
                # never proof. Preserve it until a fresh transfer is published.
                pass
            else:
                backup = settings.backup_path(candidate.task_id)
                if backup.exists():
                    shutil.rmtree(backup)
                    fsync_directory(settings.target.parent)
                if not force:
                    return RefreshResult(
                        False,
                        candidate.task_id,
                        inventory.object_count,
                        inventory.total_bytes,
                    )

        if phase == "rejected":
            rejected_id = state.get("task_id")
            try:
                rejected_id = validate_task_id(rejected_id)
            except RuntimeError:
                rejected_id = ""
            if rejected_id:
                rejected_staging = settings.staging_path(rejected_id)
                if rejected_staging.exists():
                    if not rejected_staging.is_dir() or rejected_staging.is_symlink():
                        raise RuntimeError(
                            f"refusing to remove unsafe rejected staging: {rejected_staging}"
                        )
                    shutil.rmtree(rejected_staging)
                    fsync_directory(settings.target.parent)

        selected_fields = state_provenance(settings, candidate)
        if trusted_target_proof is not None:
            selected_fields["installed_target"] = trusted_target_proof.evidence
        state = updated_state(
            {},
            clock,
            phase="selected",
            status="COMPLETE",
            **selected_fields,
        )
        save_state(settings.state_file, state)
        phase = "selected"

    task_id = candidate.task_id
    try:
        validate_completed_task(settings, task_id, candidate.task)
        completion_phase = "installing" if phase == "installing" else "complete"
        state = updated_state(
            state,
            clock,
            phase=completion_phase,
            status="COMPLETE",
            **state_provenance(settings, candidate),
        )
        save_state(settings.state_file, state)
        inventory = build_inventory(
            task_id, aws.list_export_objects(task_id), settings.export_only
        )
        validate_remote_export_metadata(aws, candidate, settings, inventory)
    except AWSCommandError:
        raise
    except RuntimeError as exc:
        if phase != "installing":
            save_rejected_state(settings, state, task_id, clock, exc)
        raise

    if resume:
        apply_interrupted_install_plan(settings, install_recovery)

    # If a prior run crashed after the swap, finish cleanup instead of downloading again.
    if resume and phase == "installing" and settings.target.exists():
        try:
            expected_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
            validate_download(
                settings.target,
                task_id,
                inventory,
                settings,
                expected_sha256,
                candidate.task,
            )
        except RuntimeError:
            pass
        else:
            try:
                finish_install(
                    settings, task_id, inventory, state, clock, candidate.task
                )
            except PermanentExportError as exc:
                save_rejected_state(settings, state, task_id, clock, exc)
                raise
            return RefreshResult(
                True, task_id, inventory.object_count, inventory.total_bytes
            )

    staging = settings.staging_path(task_id)
    staging_inventory: dict[str, int] = {}
    if staging.exists():
        if not staging.is_dir() or staging.is_symlink():
            raise RuntimeError(f"refusing to use unsafe staging path: {staging}")
        staging_inventory = local_inventory(staging)

    resume_sha256: dict[str, str] | None = None
    if state.get("sha256") is not None:
        resume_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
    discard_untrusted_reusable_files(
        staging,
        staging_inventory,
        inventory,
        resume_sha256,
    )

    ensure_download_space(settings, inventory)
    staging.mkdir(parents=True, exist_ok=True)
    state = updated_state(state, clock, phase="downloading")
    save_state(settings.state_file, state)
    aws.sync_export(task_id, staging)
    try:
        validate_download(
            staging,
            task_id,
            inventory,
            settings,
            resume_sha256,
            candidate.task,
        )
    except PermanentExportError as exc:
        save_rejected_state(settings, state, task_id, clock, exc)
        raise
    downloaded_sha256 = (
        resume_sha256
        if resume_sha256 is not None
        else sha256_inventory(staging, inventory.objects)
    )
    state = updated_state(
        state,
        clock,
        phase="downloaded",
        sha256=downloaded_sha256,
    )
    save_state(settings.state_file, state)

    state = updated_state(state, clock, phase="installing")
    save_state(settings.state_file, state)
    install_download(settings, task_id, staging)
    try:
        finish_install(settings, task_id, inventory, state, clock, candidate.task)
    except PermanentExportError as exc:
        save_rejected_state(settings, state, task_id, clock, exc)
        raise
    return RefreshResult(True, task_id, inventory.object_count, inventory.total_bytes)


def dry_run(
    settings: Settings,
    aws,
    clock: Callable[[], datetime] = utc_now,
    *,
    force: bool = False,
) -> str:
    now = clock().astimezone(timezone.utc)
    identity = aws.get_identity()
    verify_identity(settings, identity)
    state = load_state(settings.state_file)
    phase = state.get("phase")
    validate_checkpoint_artifact_paths(settings, state)
    resolve_installed_backup(settings, state, remove=False)
    install_recovery = plan_interrupted_install(settings, state)
    ensure_no_orphaned_target_backup(settings, state, install_recovery)
    trusted_target_proof = trusted_target_candidate(settings, state, install_recovery)
    trusted_target = (
        trusted_target_proof.candidate if trusted_target_proof is not None else None
    )

    plan = plan_candidate(settings, aws, state, now, trusted_target)
    candidate = plan.candidate
    inventory = build_inventory(
        candidate.task_id,
        aws.list_export_objects(candidate.task_id),
        settings.export_only,
    )
    validate_remote_export_metadata(aws, candidate, settings, inventory)
    if plan.resume:
        published = (
            phase == "installing"
            and install_recovery is not None
            and install_recovery.action == "published"
        )
        if not published:
            check_dry_run_download_space(settings, inventory)
        action = f"resume selected follower task {candidate.task_id} from phase {phase}"
        return (
            f"Dry run OK: account {identity['Account']}; would {action}; "
            f"target {settings.target}"
        )

    action = f"download latest follower task {candidate.task_id}"
    if (
        phase == "installed"
        and trusted_target is not None
        and trusted_target.task_id == candidate.task_id
    ):
        action = (
            f"force re-download follower task {candidate.task_id}"
            if force
            else f"no-op; latest follower task {candidate.task_id} is installed"
        )
    elif phase == "installed" and state_has_provenance(settings, state, candidate):
        manifest = state.get("sha256")
        if manifest is not None:
            try:
                validate_installed_snapshot(settings, candidate.task_id, manifest)
            except RuntimeError:
                action = f"migrate untrusted target to {candidate.task_id}"
            else:
                action = (
                    f"force re-download follower task {candidate.task_id}"
                    if force
                    else f"no-op; latest follower task {candidate.task_id} is installed"
                )
        else:
            action = f"migrate untrusted target to {candidate.task_id}"
    elif settings.target.exists() or phase == "installed":
        action = f"migrate existing target to {candidate.task_id}"
    if not action.startswith("no-op"):
        check_dry_run_download_space(settings, inventory)
    return (
        f"Dry run OK: account {identity['Account']}; would {action}; "
        f"target {settings.target}"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="verify identity and report the next action without mutating AWS or disk",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="force a follower re-download of the latest completed export",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    settings = Settings()
    if args.dry_run:
        try:
            aws = AWSClient(settings)
            print(dry_run(settings, aws, force=args.force))
            return 0
        except Exception as exc:  # noqa: BLE001 - dry-run must surface every failure.
            print(f"Weekly production DB follower failed: {exc}", file=sys.stderr)
            return 1

    settings.lock_file.parent.mkdir(parents=True, exist_ok=True)
    with settings.lock_file.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        try:
            aws = AWSClient(settings)
            refresh_once(settings, aws, force=args.force)
            # no-agent cron treats empty stdout as success without delivery.
            return 0
        except Exception as exc:  # noqa: BLE001 - cron must surface every hard failure.
            print(f"Weekly production DB follower failed: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
