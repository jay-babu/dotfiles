#!/usr/bin/env python3
"""Refresh /root/dev/production_db from a new production RDS S3 export.

The script is designed for a weekly Hermes no-agent cron job. It keeps the
current local snapshot until a complete replacement has downloaded with S3
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
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import NamedTuple

TASK_PREFIX = "transformity-production-no-audit-scraper-"
TASK_ID_PATTERN = re.compile(rf"{re.escape(TASK_PREFIX)}\d{{8}}-\d{{6}}")
ACTIVE_PHASES = {
    "starting",
    "waiting",
    "complete",
    "downloading",
    "downloaded",
    "installing",
}
TERMINAL_FAILURE_STATUSES = {"FAILED", "CANCELED", "CANCELLED"}
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
        source_arn: str = "arn:aws:rds:us-east-1:928004597368:cluster:transformity-production",
        export_only: tuple[str, ...] = ("postgres.reference", "postgres.public"),
        s3_bucket: str = "transformity-rds-export-backups",
        iam_role_arn: str = "arn:aws:iam::928004597368:role/service-role/rds-export",
        kms_key_arn: str = "arn:aws:kms:us-east-1:928004597368:key/af762111-98be-4740-8cc0-04e440913e0f",
        min_interval: timedelta = timedelta(days=6),
        poll_interval_seconds: int = 30,
        export_timeout_seconds: int = 40 * 60,
        sync_timeout_seconds: int = 15 * 60,
        free_space_headroom_bytes: int = 1024**3,
    ):
        self.target = target
        self.state_file = state_file
        self.lock_file = lock_file
        self.account_id = account_id
        self.region = region
        self.profile = profile
        self.source_arn = source_arn
        self.export_only = export_only
        self.s3_bucket = s3_bucket
        self.iam_role_arn = iam_role_arn
        self.kms_key_arn = kms_key_arn
        self.min_interval = min_interval
        self.poll_interval_seconds = poll_interval_seconds
        self.export_timeout_seconds = export_timeout_seconds
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

    def get_identity(self) -> dict:
        return self._run("sts", "get-caller-identity", timeout=60)

    def start_export(self, task_id: str) -> dict:
        return self._run(
            "rds",
            "start-export-task",
            "--export-task-identifier",
            task_id,
            "--source-arn",
            self.settings.source_arn,
            "--s3-bucket-name",
            self.settings.s3_bucket,
            "--iam-role-arn",
            self.settings.iam_role_arn,
            "--kms-key-id",
            self.settings.kms_key_arn,
            "--export-only",
            *self.settings.export_only,
            timeout=120,
        )

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
    explicit = os.environ.get("WEEKLY_PRODUCTION_DB_AWS_BIN")
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    # Prefer a real mise install over a shim because cron has a deliberately
    # minimal environment and should not depend on interactive shell startup.
    installs = Path("/root/.local/share/mise/installs/aws")
    if installs.is_dir():
        candidates.extend(
            sorted(
                installs.glob("*/.mise-bins/aws"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        )
    candidates.extend(
        [
            Path("/root/.local/share/mise/shims/aws"),
            Path("/usr/local/bin/aws"),
            Path("/usr/bin/aws"),
        ]
    )
    discovered = shutil.which("aws")
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise RuntimeError("AWS CLI is not installed or executable")


def clean_aws_environment(settings: Settings) -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_CREDENTIAL_EXPIRATION",
        "AWS_ROLE_ARN",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "AWS_DEFAULT_PROFILE",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "HOME": "/root",
            "AWS_PROFILE": settings.profile,
            "AWS_REGION": settings.region,
            "AWS_DEFAULT_REGION": settings.region,
            "AWS_PAGER": "",
            "AWS_EC2_METADATA_DISABLED": "true",
            "PATH": "/root/.local/share/mise/shims:/usr/local/bin:/usr/bin:/bin",
        }
    )
    return environment


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
    result["version"] = 1
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
    if not arn:
        raise RuntimeError("AWS caller identity did not include an ARN")


def new_task_id(now: datetime) -> str:
    return TASK_PREFIX + now.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")


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
    if sorted(task.get("ExportOnly", [])) != sorted(settings.export_only):
        raise RuntimeError(
            f"RDS export {task_id} has unexpected ExportOnly: {task.get('ExportOnly')!r}"
        )
    if (task.get("S3Prefix") or "") != "":
        raise RuntimeError(
            f"RDS export {task_id} has unexpected S3Prefix: {task.get('S3Prefix')!r}"
        )
    if task.get("Status") != "COMPLETE":
        raise RuntimeError(
            f"RDS export {task_id} is not complete: {task.get('Status')!r}"
        )
    if task.get("WarningMessage"):
        raise RuntimeError(
            f"RDS export {task_id} completed with a warning: "
            f"{task.get('WarningMessage')}"
        )


def is_allowed_export_data_key(relative: str, export_only: tuple[str, ...]) -> bool:
    parts = PurePosixPath(relative).parts
    if len(parts) != 4:
        return False
    database, qualified_table, partition, filename = parts
    if not partition.isdecimal():
        return False
    if filename != "_SUCCESS" and not (
        filename.startswith("part-") and filename.endswith(".parquet")
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
        rf"{re.escape(table_info_prefix)}from_\d+_to_\d+\.json"
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
    if not any(name.endswith(".parquet") for name in names):
        raise RuntimeError(f"RDS export {task_id} has no Parquet files")


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


def validate_table_metadata(
    directory: Path, task_id: str, export_only: tuple[str, ...]
) -> None:
    paths = sorted(directory.glob(f"export_tables_info_{task_id}_*.json"))
    seen_targets: set[str] = set()
    incomplete: list[str] = []
    for path in paths:
        try:
            document = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid downloaded table metadata: {path}") from exc
        if not isinstance(document, dict):
            raise RuntimeError(  # noqa: TRY004 - malformed external export metadata
                f"invalid downloaded table metadata object: {path}"
            )
        entries = document.get("perTableStatus")
        if not isinstance(entries, list) or not entries:
            raise RuntimeError(
                f"downloaded table metadata has no table statuses: {path}"
            )
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("target"), str):
                raise RuntimeError(  # noqa: TRY004 - malformed external export metadata
                    f"invalid table status in downloaded metadata: {path}"
                )
            target = entry["target"]
            if not any(target.startswith(f"{scope}.") for scope in export_only):
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


def validate_download(
    directory: Path,
    task_id: str,
    inventory: Inventory,
    export_only: tuple[str, ...],
    expected_sha256: dict[str, str] | None = None,
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
    info_path = directory / f"export_info_{task_id}.json"
    try:
        info = json.loads(info_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise PermanentExportError(
            f"invalid downloaded export metadata: {info_path}"
        ) from exc
    if not isinstance(info, dict):
        raise PermanentExportError(
            f"downloaded export metadata is not an object: {info_path}"
        )
    if info.get("exportTaskIdentifier") != task_id or info.get("status") != "COMPLETE":
        raise PermanentExportError(
            f"downloaded export metadata does not confirm {task_id}"
        )
    try:
        validate_table_metadata(directory, task_id, export_only)
    except RuntimeError as exc:
        raise PermanentExportError(str(exc)) from exc
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


def validate_installed_snapshot(
    settings: Settings,
    task_id: str,
    manifest_value: object,
) -> Inventory:
    if not settings.target.is_dir() or settings.target.is_symlink():
        raise RuntimeError(
            f"download directory is missing or unsafe: {settings.target}"
        )
    local = local_inventory(settings.target)
    validate_inventory_names(task_id, local, settings.export_only)
    inventory = Inventory(local, len(local), sum(local.values()))
    manifest = validate_sha256_manifest(manifest_value, inventory)
    validate_download(
        settings.target,
        task_id,
        inventory,
        settings.export_only,
        manifest,
    )
    return inventory


def ensure_download_space(settings: Settings, inventory: Inventory) -> None:
    settings.target.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(settings.target.parent).free
    # Checksum-aware sync may still redownload manifest-matching files based on
    # timestamps and writes through temporary files. Reserve the complete export
    # rather than crediting staging bytes that might coexist with a replacement.
    required = inventory.total_bytes + settings.free_space_headroom_bytes
    if free < required:
        raise RuntimeError(
            f"not enough free disk for export: need {required / 1024**3:.2f} GiB, "
            f"have {free / 1024**3:.2f} GiB"
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


def restore_interrupted_target(settings: Settings, task_id: str) -> None:
    backup = settings.backup_path(task_id)
    if settings.target.exists() or not backup.exists():
        return
    if not backup.is_dir() or backup.is_symlink():
        raise RuntimeError(f"refusing to restore unsafe replacement backup: {backup}")
    backup.rename(settings.target)
    fsync_directory(settings.target.parent)


def directory_declares_export(directory: Path, task_id: str) -> bool:
    if not directory.is_dir() or directory.is_symlink():
        raise RuntimeError(f"unsafe snapshot directory during recovery: {directory}")
    info_path = directory / f"export_info_{task_id}.json"
    try:
        info = json.loads(info_path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(info, dict):
        return False
    return info.get("exportTaskIdentifier") == task_id


def recover_interrupted_install_paths(settings: Settings, task_id: str) -> None:
    """Restore old target orientation after a crash during rollback."""
    target = settings.target
    staging = settings.staging_path(task_id)
    backup = settings.backup_path(task_id)
    target_is_new = directory_declares_export(target, task_id)

    if backup.exists():
        if staging.exists():
            raise RuntimeError(
                f"ambiguous install recovery with staging and backup present: {task_id}"
            )
        backup_is_new = directory_declares_export(backup, task_id)
        if target_is_new == backup_is_new:
            raise RuntimeError(f"cannot determine backup orientation for {task_id}")
        if target_is_new:
            atomic_exchange(target, backup)
            fsync_directory(target.parent)
        backup.rename(staging)
        fsync_directory(target.parent)
        return

    if staging.exists():
        staging_is_new = directory_declares_export(staging, task_id)
        if target_is_new == staging_is_new:
            raise RuntimeError(f"cannot determine staging orientation for {task_id}")
        if target_is_new:
            atomic_exchange(target, staging)
            fsync_directory(target.parent)
        return

    if target_is_new:
        target.rename(staging)
        fsync_directory(target.parent)


def finish_install(
    settings: Settings,
    task_id: str,
    inventory: Inventory,
    state: dict,
    clock: Callable[[], datetime],
) -> dict:
    backup = settings.backup_path(task_id)
    staging = settings.staging_path(task_id)
    try:
        expected_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
        validate_download(
            settings.target,
            task_id,
            inventory,
            settings.export_only,
            expected_sha256,
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
    sleeper: Callable[[float], None] = time.sleep,
) -> RefreshResult:
    now = clock().astimezone(timezone.utc)
    verify_identity(settings, aws.get_identity())
    state = load_state(settings.state_file)
    phase = state.get("phase")
    saved_task_id = state.get("task_id")
    if phase in ACTIVE_PHASES or phase in {"installed", "rejected"}:
        validate_task_id(saved_task_id)

    if phase == "rejected":
        rejected_task_id = str(saved_task_id)
        rejected_backup = settings.backup_path(rejected_task_id)
        if rejected_backup.exists():
            raise RuntimeError(
                f"rejected export still has a backup requiring inspection: {rejected_backup}"
            )
        rejected_staging = settings.staging_path(rejected_task_id)
        if rejected_staging.exists():
            if not rejected_staging.is_dir() or rejected_staging.is_symlink():
                raise RuntimeError(
                    f"refusing to remove unsafe rejected staging: {rejected_staging}"
                )
            shutil.rmtree(rejected_staging)
            fsync_directory(settings.target.parent)

    if phase == "installed":
        installed_at = parse_timestamp(state.get("installed_at"))
        installed_task_id = str(state.get("task_id", ""))
        backup = settings.backup_path(installed_task_id)
        checksum_state = state.get("sha256")
        if checksum_state is None:
            raise RuntimeError(
                "installed state does not have a trusted local SHA-256 manifest; "
                "refusing to bless the current snapshot without a verified transfer"
            )
        # The committed local manifest is the proof for the installed snapshot.
        # Do not couple local availability to RDS task history or S3 objects that
        # may have been removed later by the independently managed lifecycle rule.
        validate_installed_snapshot(settings, installed_task_id, checksum_state)
        if backup.exists():
            shutil.rmtree(backup)
            fsync_directory(settings.target.parent)
        if (
            not force
            and installed_at is not None
            and now - installed_at < settings.min_interval
        ):
            return RefreshResult(False, installed_task_id)

    task_id = str(state.get("task_id", "")) if phase in ACTIVE_PHASES else ""
    task = None
    if task_id:
        if phase == "installing":
            restore_interrupted_target(settings, task_id)
        task = aws.describe_export(task_id)
        if task is None and phase != "starting":
            raise RuntimeError(f"saved RDS export task no longer exists: {task_id}")

    if not task_id:
        task_id = new_task_id(now)
        state = updated_state(
            {},
            clock,
            phase="starting",
            task_id=task_id,
            started_at=now.isoformat(),
        )
        save_state(settings.state_file, state)

    if task is None:
        task = aws.start_export(task_id)
        state = updated_state(state, clock, phase="waiting", status=task.get("Status"))
        save_state(settings.state_file, state)

    deadline = time.monotonic() + settings.export_timeout_seconds
    while task.get("Status") != "COMPLETE":
        status = str(task.get("Status", "UNKNOWN"))
        if status in TERMINAL_FAILURE_STATUSES:
            state = updated_state(
                state,
                clock,
                phase="failed",
                status=status,
                failure_cause=task.get("FailureCause"),
            )
            save_state(settings.state_file, state)
            raise RuntimeError(
                f"RDS export {task_id} ended in {status}: "
                f"{task.get('FailureCause') or 'no failure cause supplied'}"
            )
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"RDS export {task_id} did not finish within "
                f"{settings.export_timeout_seconds}s (status={status})"
            )
        state = updated_state(
            state,
            clock,
            phase="waiting",
            status=status,
            percent_progress=task.get("PercentProgress"),
        )
        save_state(settings.state_file, state)
        sleeper(settings.poll_interval_seconds)
        task = aws.describe_export(task_id)
        if task is None:
            raise RuntimeError(f"RDS export task disappeared while waiting: {task_id}")

    try:
        validate_completed_task(settings, task_id, task)
        # Preserve the transactional recovery checkpoint. Downgrading
        # "installing" to "complete" here can strand a published target beside
        # its backup if the process exits before finish_install records success.
        completion_phase = "installing" if phase == "installing" else "complete"
        state = updated_state(state, clock, phase=completion_phase, status="COMPLETE")
        save_state(settings.state_file, state)
        inventory = build_inventory(
            task_id, aws.list_export_objects(task_id), settings.export_only
        )
    except AWSCommandError:
        # AWS CLI failures are transient. Preserve the current checkpoint so a
        # retry can resume the same task and, for installing, retain the old
        # snapshot until publication has been durably validated.
        raise
    except RuntimeError as exc:
        # An installing checkpoint may be between atomic rename steps. Marking
        # it rejected could make the rejected-state cleanup delete the only old
        # snapshot still parked under the staging name.
        if phase != "installing":
            save_rejected_state(settings, state, task_id, clock, exc)
        raise

    # If a prior run crashed after the swap, finish cleanup instead of downloading again.
    if phase == "installing" and settings.target.exists():
        try:
            expected_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
            validate_download(
                settings.target,
                task_id,
                inventory,
                settings.export_only,
                expected_sha256,
            )
        except RuntimeError:
            recover_interrupted_install_paths(settings, task_id)
        else:
            try:
                finish_install(settings, task_id, inventory, state, clock)
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
        # Reject nested symlinks before allowing AWS CLI to reuse the directory.
        staging_inventory = local_inventory(staging)

    resume_sha256: dict[str, str] | None = None
    if state.get("sha256") is not None:
        resume_sha256 = validate_sha256_manifest(state.get("sha256"), inventory)
    # AWS CLI can skip equal-size/equal-mtime files even in checksum mode. Only
    # retain complete staging files when a trusted manifest proves their bytes.
    staging_inventory = discard_untrusted_reusable_files(
        staging,
        staging_inventory,
        inventory,
        resume_sha256,
    )

    ensure_download_space(settings, inventory)
    staging.mkdir(parents=True, exist_ok=True)
    state = updated_state(state, clock, phase="downloading")
    save_state(settings.state_file, state)
    # Always invoke checksum-aware sync, even for a size-complete staging tree.
    # A same-size corruption after an interrupted run must not bypass S3 checksums.
    aws.sync_export(task_id, staging)
    try:
        validate_download(
            staging,
            task_id,
            inventory,
            settings.export_only,
            resume_sha256,
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
        finish_install(settings, task_id, inventory, state, clock)
    except PermanentExportError as exc:
        save_rejected_state(settings, state, task_id, clock, exc)
        raise
    return RefreshResult(True, task_id, inventory.object_count, inventory.total_bytes)


def dry_run(settings: Settings, aws, clock: Callable[[], datetime] = utc_now) -> str:
    now = clock().astimezone(timezone.utc)
    identity = aws.get_identity()
    verify_identity(settings, identity)
    state = load_state(settings.state_file)
    phase = state.get("phase")
    task_id = str(state.get("task_id", ""))
    if phase in ACTIVE_PHASES and task_id:
        action = f"resume {task_id} from phase {phase}"
    elif phase == "installed":
        installed_at = parse_timestamp(state.get("installed_at"))
        if installed_at is not None and now - installed_at < settings.min_interval:
            action = f"skip recent installed export {task_id}"
        else:
            action = f"start {new_task_id(now)}"
    else:
        action = f"start {new_task_id(now)}"
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
        help="start a new export even when the last installation is less than six days old",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    settings = Settings()
    settings.lock_file.parent.mkdir(parents=True, exist_ok=True)
    with settings.lock_file.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        try:
            aws = AWSClient(settings)
            if args.dry_run:
                print(dry_run(settings, aws))
                return 0
            refresh_once(settings, aws, force=args.force)
            # no-agent cron treats empty stdout as success without delivery.
            return 0
        except Exception as exc:  # noqa: BLE001 - cron must surface every hard failure.
            print(f"Weekly production DB export failed: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
