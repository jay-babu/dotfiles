from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "private_dot_hermes"
    / "scripts"
    / "private_executable_weekly_production_db_export.py"
)
CRON_JOBS = ROOT / "private_dot_hermes" / "private_cron" / "private_jobs.json"

spec = importlib.util.spec_from_file_location("weekly_production_db_export", SCRIPT)
assert spec is not None and spec.loader is not None
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

TASK_LATEST = "transformity-no-audit-scraper-205b8e797b149e711ce2e19d797e57"
TASK_OLDER = "transformity-no-audit-scraper-ffffffffffffffffffffffffffffff"
TASK_PREVIOUS_WEEK = "transformity-no-audit-scraper-692f293fa31a9012fdfd0d284fc173"
TASK_FOREIGN = "transformity-no-audit-scraper-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
LEGACY_TASK = "transformity-production-no-audit-scraper-20260809-110017"
LATEST_COMPLETED = datetime(2026, 8, 16, 11, 19, 26, tzinfo=timezone.utc)
OLDER_COMPLETED = datetime(2026, 8, 16, 11, 0, 0, tzinfo=timezone.utc)


class FakeAWS:
    def __init__(self, settings, *, tasks=None, sync_error=None, identity_arn=None):
        self.settings = settings
        self.warning_message: str | None = None
        self.tasks = list(tasks if tasks is not None else [self.task(TASK_LATEST)])
        self.sync_error = sync_error
        self.identity_arn = identity_arn or (
            f"arn:aws:sts::{settings.account_id}:assumed-role/"
            "HermesAgentReadOnly/hermes-agent-production"
        )
        self.synced: list[str] = []
        self.list_calls = 0
        self.described: list[str] = []
        self.list_error: Exception | None = None
        self.describe_error: Exception | None = None
        self.omit_parquet = False
        self.omit_checksum = False
        self.warning_message: str | None = None
        self.table_status = "COMPLETE"
        self.extra_scope_object = False
        self.extra_table_target = False
        self.nested_metadata_key = False
        self.malformed_data_key = False
        self.foreign_metadata_name = False
        self.missing_success = False
        self.partition_without_success = False
        self.unlisted_data_table = False
        self.omit_reference_partition = False
        self.public_metadata_target = "postgres.public.example"
        self.all_tables_empty = False
        self.export_info_changes: dict[str, object] = {}

    def task(
        self,
        task_id=TASK_LATEST,
        *,
        completed_at=None,
        started_at=None,
        **changes,
    ):
        if completed_at is None:
            completed_at = {
                TASK_LATEST: LATEST_COMPLETED,
                TASK_OLDER: OLDER_COMPLETED,
                TASK_PREVIOUS_WEEK: datetime(
                    2026, 8, 9, 11, 19, 0, tzinfo=timezone.utc
                ),
            }.get(task_id, OLDER_COMPLETED)
        if started_at is None:
            started_at = completed_at - timedelta(minutes=20)
        task = {
            "ExportTaskIdentifier": task_id,
            "SourceArn": self.settings.source_arn,
            "ExportOnly": list(self.settings.export_only),
            "S3Bucket": self.settings.s3_bucket,
            "S3Prefix": "",
            "IamRoleArn": self.settings.iam_role_arn,
            "KmsKeyId": self.settings.kms_key_arn,
            "Status": "COMPLETE",
            "PercentProgress": 100,
            "WarningMessage": self.warning_message,
            "TaskStartTime": started_at.isoformat(),
            "TaskEndTime": completed_at.isoformat(),
            "TotalExtractedDataInGB": 0,
        }
        task.update(changes)
        return task

    def get_identity(self):
        return {"Account": self.settings.account_id, "Arn": self.identity_arn}

    def list_export_tasks(self):
        self.list_calls += 1
        if self.list_error is not None:
            raise self.list_error
        return self.tasks

    def describe_export(self, task_id):
        self.described.append(task_id)
        if self.describe_error is not None:
            raise self.describe_error
        return next(
            (task for task in self.tasks if task["ExportTaskIdentifier"] == task_id),
            None,
        )

    def list_export_objects(self, task_id):
        if self.list_error is not None:
            raise self.list_error
        result = []
        for key, value in self._objects(task_id).items():
            item = {"Key": key, "Size": len(value)}
            if not self.omit_checksum:
                item["ChecksumAlgorithm"] = ["CRC64NVME"]
            result.append(item)
        return result

    def get_export_metadata(self, task_id, names):
        objects = self._objects(task_id)
        prefix = f"{task_id}/"
        return {name: json.loads(objects[prefix + name]) for name in names}

    def sync_export(self, task_id, destination):
        self.synced.append(task_id)
        if self.sync_error:
            raise self.sync_error
        prefix = f"{task_id}/"
        destination.mkdir(parents=True, exist_ok=True)
        for key, value in self._objects(task_id).items():
            path = destination / key.removeprefix(prefix)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)

    def _objects(self, task_id):
        prefix = f"{task_id}/"
        metadata_task = TASK_FOREIGN if self.foreign_metadata_name else task_id
        selected_task = next(
            (task for task in self.tasks if task["ExportTaskIdentifier"] == task_id),
            self.task(task_id),
        )
        table_statuses = [
            {"target": self.public_metadata_target, "status": self.table_status},
            {"target": "postgres.reference.example", "status": "COMPLETE"},
        ]
        if self.extra_table_target:
            table_statuses.append(
                {"target": "postgres.private.secret", "status": "COMPLETE"}
            )
        export_info = {
            "exportTaskIdentifier": metadata_task,
            "sourceArn": self.settings.source_arn,
            "exportOnly": list(reversed(self.settings.export_only)),
            "s3Bucket": self.settings.s3_bucket,
            "s3Prefix": "",
            "exportedFilesPath": task_id,
            "iamRoleArn": self.settings.iam_role_arn,
            "kmsKeyId": self.settings.kms_key_arn,
            "status": "COMPLETE",
            "percentProgress": 100,
            "taskStartTime": selected_task["TaskStartTime"],
            "taskEndTime": selected_task["TaskEndTime"],
            "totalExportedDataInGB": selected_task["TotalExtractedDataInGB"] + 0.25,
        }
        export_info.update(self.export_info_changes)
        objects = {
            prefix + f"export_info_{metadata_task}.json": json.dumps(
                export_info
            ).encode(),
            prefix + f"export_tables_info_{metadata_task}_from_1_to_2.json": json.dumps(
                {"perTableStatus": table_statuses}
            ).encode(),
        }
        if not self.missing_success:
            objects[prefix + "postgres/public.example/1/_SUCCESS"] = b""
        if not self.all_tables_empty and not self.omit_parquet:
            objects[prefix + "postgres/public.example/1/part-00000.gz.parquet"] = (
                b"PAR1test"
            )
        if not self.omit_reference_partition:
            objects[prefix + "postgres/reference.example/1/_SUCCESS"] = b""
        if self.partition_without_success:
            objects[prefix + "postgres/public.example/2/part-00000.gz.parquet"] = (
                b"PAR1second"
            )
        if self.unlisted_data_table:
            objects[prefix + "postgres/public.unlisted/1/_SUCCESS"] = b""
            objects[prefix + "postgres/public.unlisted/1/part-00000.gz.parquet"] = (
                b"PAR1unlisted"
            )
        if self.extra_scope_object:
            objects[prefix + "postgres/private.secret/1/part-00000.gz.parquet"] = (
                b"PAR1secret"
            )
        if self.nested_metadata_key:
            objects[
                prefix + f"export_tables_info_{task_id}_shadow/postgres/private.json"
            ] = b"invalid"
        if self.malformed_data_key:
            objects[prefix + "postgres/public.example/1/not-parquet.txt"] = b"invalid"
        return objects


class WeeklyProductionDBFollowerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        root = Path(self.tempdir.name)
        self.target = root / "production_db"
        self.state_file = root / "state" / "weekly_export.json"
        self.settings = exporter.Settings(
            target=self.target,
            state_file=self.state_file,
            lock_file=root / "state" / "weekly_export.lock",
            max_export_age=timedelta(hours=48),
        )
        self.now = datetime(2026, 8, 16, 13, 0, tzinfo=timezone.utc)

    def run_refresh(self, aws, *, force=False):
        return exporter.refresh_once(
            self.settings,
            aws,
            force=force,
            clock=lambda: self.now,
        )

    @staticmethod
    def checksum_manifest(aws, task_id):
        prefix = f"{task_id}/"
        return {
            key.removeprefix(prefix): hashlib.sha256(value).hexdigest()
            for key, value in aws._objects(task_id).items()
        }

    def write_installed_state(self, aws, task_id=TASK_LATEST, *, trusted=True):
        if self.target.exists():
            import shutil

            shutil.rmtree(self.target)
        aws.sync_export(task_id, self.target)
        aws.synced.clear()
        task = next(
            task for task in aws.tasks if task["ExportTaskIdentifier"] == task_id
        )
        state = {
            "version": 2,
            "phase": "installed",
            "task_id": task_id,
            "task_timestamp": task["TaskEndTime"],
            "installed_at": self.now.isoformat(),
            "source_arn": self.settings.source_arn,
            "s3_bucket": self.settings.s3_bucket,
            "export_only": list(self.settings.export_only),
            "iam_role_arn": self.settings.iam_role_arn,
            "kms_key_arn": self.settings.kms_key_arn,
        }
        if trusted:
            state["sha256"] = self.checksum_manifest(aws, task_id)
        exporter.save_state(self.state_file, state)

    def write_active_state(self, task, phase="downloading", **changes):
        state = {
            "version": 2,
            "phase": phase,
            "task_id": task["ExportTaskIdentifier"],
            "task_timestamp": task["TaskEndTime"],
            "source_arn": self.settings.source_arn,
            "s3_bucket": self.settings.s3_bucket,
            "export_only": list(self.settings.export_only),
            "iam_role_arn": self.settings.iam_role_arn,
            "kms_key_arn": self.settings.kms_key_arn,
        }
        state.update(changes)
        exporter.save_state(self.state_file, state)

    def test_managed_cron_job_has_follower_contract_without_runtime_state(self):
        payload = json.loads(CRON_JOBS.read_text())
        job = next(
            job
            for job in payload["jobs"]
            if job["name"] == "Weekly production DB RDS export refresh"
        )

        self.assertEqual(
            job["schedule"],
            {"kind": "cron", "expr": "0 9 * * 0", "display": "0 9 * * 0"},
        )
        self.assertEqual(job["schedule_display"], "0 9 * * 0")
        self.assertEqual(job["repeat"], {"times": None})
        self.assertTrue(job["enabled"])
        self.assertTrue(job["no_agent"])
        self.assertEqual(job["deliver"], "origin")
        self.assertIn("follower", job["prompt"].lower())
        self.assertIn("Temporal", job["prompt"])
        self.assertNotIn("start", job["prompt"].lower())
        for key in (
            "next_run_at",
            "last_run_at",
            "last_status",
            "last_error",
            "last_delivery_error",
            "fire_claim",
            "state",
            "paused_at",
            "paused_reason",
        ):
            self.assertNotIn(key, job)

    def test_temporal_task_identifier_grammar_is_exact(self):
        self.assertEqual(exporter.validate_task_id(TASK_LATEST), TASK_LATEST)
        for invalid in (
            LEGACY_TASK,
            "transformity-no-audit-scraper-205B8E797B149E711CE2E19D797E57",
            "transformity-no-audit-scraper-205b",
            "../" + TASK_LATEST,
        ):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                exporter.validate_task_id(invalid)

    def test_identity_is_pinned_to_exact_read_only_assumed_role_shape(self):
        allowed = FakeAWS(self.settings).get_identity()
        exporter.verify_identity(self.settings, allowed)
        for arn in (
            f"arn:aws:iam::{self.settings.account_id}:role/HermesAgentReadOnly",
            f"arn:aws:sts::{self.settings.account_id}:assumed-role/Admin/hermes-agent",
            f"arn:aws:sts::{self.settings.account_id}:assumed-role/HermesAgentReadOnly/hermes-agent",
            f"arn:aws:sts::{self.settings.account_id}:assumed-role/HermesAgentReadOnly/",
            "arn:aws:sts::111111111111:assumed-role/HermesAgentReadOnly/hermes-agent",
        ):
            with self.subTest(arn=arn), self.assertRaises(RuntimeError):
                exporter.verify_identity(
                    self.settings, {"Account": self.settings.account_id, "Arn": arn}
                )

    def test_aws_environment_pins_profile_files_and_removes_endpoint_overrides(self):
        ambient = {
            "AWS_ACCESS_KEY_ID": "ambient",
            "AWS_SECRET_ACCESS_KEY": "ambient",
            "AWS_SESSION_TOKEN": "ambient",
            "AWS_ENDPOINT_URL": "https://example.invalid",
            "AWS_ENDPOINT_URL_S3": "https://example.invalid",
            "AWS_ENDPOINT_URL_RDS": "https://example.invalid",
            "AWS_ENDPOINT_URL_STS": "https://example.invalid",
            "AWS_CONFIG_FILE": "/tmp/untrusted-config",
            "AWS_SHARED_CREDENTIALS_FILE": "/tmp/untrusted-credentials",
            "AWS_CREDENTIAL_FILE": "/tmp/legacy-credentials",
            "AWS_CREDENTIALS_FILE": "/tmp/other-legacy-credentials",
            "AWS_SECURITY_TOKEN": "legacy-token",
            "AWS_ROLE_SESSION_NAME": "ambient-session",
            "AWS_SDK_LOAD_CONFIG": "0",
            "AWS_CONTAINER_AUTHORIZATION_TOKEN": "container-token",
            "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE": "/tmp/container-token",
            "AWS_USE_FIPS_ENDPOINT": "true",
            "AWS_USE_DUALSTACK_ENDPOINT": "true",
            "AWS_ACCOUNT_ID": "111111111111",
            "AWS_ACCOUNT_ID_ENDPOINT_MODE": "required",
            "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true",
            "AWS_CA_BUNDLE": "/tmp/untrusted-ca.pem",
            "AWS_DATA_PATH": "/tmp/untrusted-models",
            "AWS_FUTURE_PROVIDER_SELECTOR": "ambient",
            "BOTO_CONFIG": "/tmp/untrusted-boto-config",
            "HTTPS_PROXY": "http://127.0.0.1:9999",
            "SSL_CERT_FILE": "/tmp/untrusted-cert.pem",
            "REQUESTS_CA_BUNDLE": "/tmp/untrusted-ca.pem",
            "CURL_CA_BUNDLE": "/tmp/untrusted-curl-ca.pem",
        }
        with mock.patch.dict(os.environ, ambient, clear=True):
            environment = exporter.clean_aws_environment(self.settings)

        for key in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_ENDPOINT_URL",
            "AWS_ENDPOINT_URL_S3",
            "AWS_ENDPOINT_URL_RDS",
            "AWS_ENDPOINT_URL_STS",
            "AWS_CREDENTIAL_FILE",
            "AWS_CREDENTIALS_FILE",
            "AWS_SECURITY_TOKEN",
            "AWS_ROLE_SESSION_NAME",
            "AWS_SDK_LOAD_CONFIG",
            "AWS_CONTAINER_AUTHORIZATION_TOKEN",
            "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE",
            "AWS_USE_FIPS_ENDPOINT",
            "AWS_USE_DUALSTACK_ENDPOINT",
            "AWS_ACCOUNT_ID",
            "AWS_ACCOUNT_ID_ENDPOINT_MODE",
            "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS",
            "AWS_CA_BUNDLE",
            "AWS_DATA_PATH",
            "AWS_FUTURE_PROVIDER_SELECTOR",
            "HTTPS_PROXY",
            "SSL_CERT_FILE",
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE",
        ):
            self.assertNotIn(key, environment)
        self.assertEqual(environment["AWS_PROFILE"], "production")
        self.assertEqual(environment["AWS_CONFIG_FILE"], "/root/.aws/config")
        self.assertEqual(environment["AWS_SHARED_CREDENTIALS_FILE"], "/dev/null")
        self.assertEqual(environment["BOTO_CONFIG"], "/dev/null")

    def test_aws_client_exposes_no_export_or_aws_mutation_method(self):
        client = exporter.AWSClient(self.settings, binary="/usr/bin/aws")
        self.assertFalse(hasattr(client, "start_export"))
        source = SCRIPT.read_text()
        for forbidden in (
            "start-export-task",
            "iam:PassRole",
            "create-grant",
            "retire-grant",
            "revoke-grant",
            "WEEKLY_PRODUCTION_DB_AWS_BIN",
        ):
            self.assertNotIn(forbidden, source)
        with mock.patch.object(exporter.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "not read-only allowlisted"):
                client._run("s3api", "delete-object", timeout=1)
            with self.assertRaisesRegex(RuntimeError, "pinned bucket to disk"):
                client._run(
                    "s3",
                    "sync",
                    "/tmp/local-source",
                    f"s3://{self.settings.s3_bucket}/upload",
                    timeout=1,
                    json_output=False,
                )
            with self.assertRaisesRegex(RuntimeError, "pinned bucket to stdout"):
                client._run_text(
                    "s3",
                    "cp",
                    "/tmp/local-source",
                    f"s3://{self.settings.s3_bucket}/upload",
                    timeout=1,
                )
            run.assert_not_called()

    def test_list_export_tasks_is_scoped_to_exact_source(self):
        client = exporter.AWSClient(self.settings, binary="/usr/bin/aws")
        completed = subprocess.CompletedProcess(
            [], 0, stdout='{"ExportTasks": []}', stderr=""
        )
        with mock.patch.object(
            exporter.subprocess, "run", return_value=completed
        ) as run:
            self.assertEqual(client.list_export_tasks(), [])
        command = run.call_args.args[0]
        self.assertIn("describe-export-tasks", command)
        source_option = command.index("--source-arn")
        self.assertEqual(command[source_option + 1], self.settings.source_arn)

    def test_newest_candidate_is_selected_by_completion_timestamp_not_identifier(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        selected = exporter.select_latest_completed_export(
            self.settings, aws.list_export_tasks(), self.now
        )
        self.assertEqual(selected.task_id, TASK_LATEST)
        self.assertEqual(selected.timestamp, LATEST_COMPLETED)

    def test_newest_selection_fails_closed_on_equal_timestamps(self):
        aws = FakeAWS(self.settings)
        tasks = [
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
            aws.task(TASK_OLDER, completed_at=LATEST_COMPLETED),
        ]
        with self.assertRaisesRegex(RuntimeError, "share the newest timestamp"):
            exporter.select_latest_completed_export(self.settings, tasks, self.now)

    def test_candidate_uses_start_timestamp_when_completion_timestamp_is_absent(self):
        aws = FakeAWS(self.settings)
        task = aws.task(TASK_LATEST)
        del task["TaskEndTime"]
        selected = exporter.select_latest_completed_export(
            self.settings, [task], self.now
        )
        self.assertEqual(
            selected.timestamp,
            datetime.fromisoformat(task["TaskStartTime"]).astimezone(timezone.utc),
        )

    def test_newest_temporal_candidate_must_match_every_provenance_field(self):
        aws = FakeAWS(self.settings)
        mutations = {
            "SourceArn": "arn:wrong",
            "S3Bucket": "legacy-bucket",
            "S3Prefix": "nested",
            "ExportOnly": ["postgres.public"],
            "IamRoleArn": "arn:wrong",
            "KmsKeyId": "arn:wrong",
            "WarningMessage": "skipped tables",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                task = aws.task(TASK_LATEST, **{field: value})
                with self.assertRaises(RuntimeError):
                    exporter.select_latest_completed_export(
                        self.settings, [task], self.now
                    )

    def test_noncomplete_and_foreign_identifier_tasks_are_not_candidates(self):
        aws = FakeAWS(self.settings)
        tasks = [
            aws.task(TASK_LATEST, Status="STARTING"),
            aws.task(LEGACY_TASK),
        ]
        with self.assertRaisesRegex(RuntimeError, "no qualifying completed"):
            exporter.select_latest_completed_export(self.settings, tasks, self.now)

    def test_stale_latest_export_fails_instead_of_hiding_missed_upstream_run(self):
        aws = FakeAWS(self.settings, tasks=[])
        aws.tasks = [aws.task(TASK_PREVIOUS_WEEK)]
        with self.assertRaisesRegex(RuntimeError, "older than"):
            self.run_refresh(aws)
        self.assertEqual(aws.synced, [])

    def test_list_and_describe_errors_fail_closed(self):
        aws = FakeAWS(self.settings)
        aws.list_error = exporter.AWSCommandError("list denied")
        with self.assertRaisesRegex(exporter.AWSCommandError, "list denied"):
            self.run_refresh(aws)

        aws = FakeAWS(self.settings)
        exporter.save_state(
            self.state_file,
            {
                "version": 2,
                "phase": "downloading",
                "task_id": TASK_LATEST,
                "task_timestamp": LATEST_COMPLETED.isoformat(),
            },
        )
        aws.describe_error = exporter.AWSCommandError("describe denied")
        with self.assertRaisesRegex(exporter.AWSCommandError, "describe denied"):
            self.run_refresh(aws)

    def test_replaces_existing_directory_only_after_valid_follower_download(self):
        (self.target / "analysis").mkdir(parents=True)
        (self.target / "analysis" / "old.txt").write_text("old")
        aws = FakeAWS(self.settings)

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertFalse((self.target / "analysis" / "old.txt").exists())
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "installed")
        self.assertEqual(state["task_id"], TASK_LATEST)
        self.assertEqual(state["task_timestamp"], LATEST_COMPLETED.isoformat())
        self.assertEqual(state["s3_bucket"], self.settings.s3_bucket)
        self.assertIn("sha256", state)

    def test_installed_current_task_with_trusted_manifest_is_silent_noop(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)

        result = self.run_refresh(aws)

        self.assertFalse(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [])
        self.assertEqual(aws.list_calls, 1)

    def test_newer_upstream_replaces_recent_install_regardless_of_old_interval(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_OLDER)

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [TASK_LATEST])

    def test_prior_installed_backup_is_validated_and_removed_before_new_task(self):
        import shutil

        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_OLDER)
        old_backup = self.settings.backup_path(TASK_OLDER)
        shutil.copytree(self.target, old_backup)
        real_rmtree = shutil.rmtree

        def fail_old_backup(path, *args, **kwargs):
            if Path(path) == old_backup:
                raise OSError("simulated old backup cleanup failure")
            return real_rmtree(path, *args, **kwargs)

        with (
            mock.patch.object(exporter.shutil, "rmtree", side_effect=fail_old_backup),
            self.assertRaisesRegex(OSError, "old backup cleanup failure"),
        ):
            self.run_refresh(aws)

        self.assertEqual(aws.synced, [])
        self.assertTrue(old_backup.exists())
        self.assertTrue((self.target / f"export_info_{TASK_OLDER}.json").is_file())

        result = self.run_refresh(aws)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertFalse(old_backup.exists())
        self.assertEqual(aws.synced, [TASK_LATEST])

    def test_invalid_installed_target_preserves_prior_backup_and_blocks_advance(self):
        import shutil

        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_OLDER)
        old_backup = self.settings.backup_path(TASK_OLDER)
        shutil.copytree(self.target, old_backup)
        next(self.target.rglob("*.parquet")).write_bytes(b"corrupt!")

        with self.assertRaisesRegex(
            RuntimeError, "installed target before backup cleanup"
        ):
            self.run_refresh(aws)

        self.assertTrue(old_backup.exists())
        self.assertEqual(aws.synced, [])

    def test_replayed_active_state_cannot_orphan_canonical_target_backup(self):
        import shutil

        aws = FakeAWS(self.settings)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        older = aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED)
        aws.tasks = [latest, older]
        self.write_installed_state(aws, TASK_LATEST)
        backup = self.settings.backup_path(TASK_LATEST)
        shutil.copytree(self.target, backup)
        self.write_active_state(older)

        with self.assertRaisesRegex(RuntimeError, "unresolved backup residue"):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        with self.assertRaisesRegex(RuntimeError, "unresolved backup residue"):
            self.run_refresh(aws)

        self.assertTrue(backup.exists())
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertEqual(aws.synced, [])
        self.assertEqual(json.loads(self.state_file.read_text())["task_id"], TASK_OLDER)

    def test_force_redownloads_latest_but_never_starts_an_export(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        result = self.run_refresh(aws, force=True)
        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [TASK_LATEST])

    def test_legacy_state_and_mismatched_target_are_preserved_on_download_failure(self):
        self.target.mkdir()
        (self.target / f"export_info_{TASK_PREVIOUS_WEEK}.json").write_text(
            json.dumps(
                {"exportTaskIdentifier": TASK_PREVIOUS_WEEK, "status": "COMPLETE"}
            )
        )
        (self.target / "only-old-copy.txt").write_text("keep")
        exporter.save_state(
            self.state_file,
            {"version": 1, "phase": "installed", "task_id": LEGACY_TASK},
        )
        aws = FakeAWS(
            self.settings,
            tasks=[
                FakeAWS(self.settings).task(TASK_PREVIOUS_WEEK),
                FakeAWS(self.settings).task(TASK_LATEST),
            ],
            sync_error=RuntimeError("simulated follower failure"),
        )

        with self.assertRaisesRegex(RuntimeError, "simulated follower failure"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "only-old-copy.txt").read_text(), "keep")
        self.assertEqual(
            json.loads(self.state_file.read_text())["task_id"], TASK_LATEST
        )

    def test_legacy_state_is_replaced_only_after_fresh_temporal_export_is_validated(
        self,
    ):
        self.target.mkdir()
        (self.target / "only-old-copy.txt").write_text("keep")
        exporter.save_state(
            self.state_file,
            {"version": 1, "phase": "installed", "task_id": LEGACY_TASK},
        )
        aws = FakeAWS(self.settings)

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertFalse((self.target / "only-old-copy.txt").exists())
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())

    def test_untrusted_or_mismatched_current_target_is_not_blessed(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws, trusted=False)
        (self.target / "untrusted.txt").write_text("untrusted")

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertFalse((self.target / "untrusted.txt").exists())

    def test_resume_keeps_selected_task_even_when_newer_task_appears(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [aws.task(TASK_OLDER), aws.task(TASK_LATEST)]
        exporter.save_state(
            self.state_file,
            {
                "version": 2,
                "phase": "downloading",
                "task_id": TASK_OLDER,
                "task_timestamp": OLDER_COMPLETED.isoformat(),
                "source_arn": self.settings.source_arn,
                "s3_bucket": self.settings.s3_bucket,
                "export_only": list(self.settings.export_only),
                "iam_role_arn": self.settings.iam_role_arn,
                "kms_key_arn": self.settings.kms_key_arn,
            },
        )

        result = self.run_refresh(aws)

        self.assertEqual(result.task_id, TASK_OLDER)
        self.assertEqual(aws.synced, [TASK_OLDER])
        self.assertEqual(aws.list_calls, 0)
        self.assertEqual(aws.described, [TASK_OLDER])

    def test_active_checkpoint_cannot_replace_a_newer_declared_target(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_LATEST)
        self.write_active_state(aws.tasks[0])

        result = self.run_refresh(aws)

        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertFalse((self.target / f"export_info_{TASK_OLDER}.json").exists())

    def test_malformed_active_checkpoint_still_protects_newer_declared_target(self):
        aws = FakeAWS(self.settings)
        older = aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        aws.tasks = [older, latest]
        self.write_installed_state(aws, TASK_LATEST)
        self.write_active_state(older)
        state = json.loads(self.state_file.read_text())
        del state["task_timestamp"]
        exporter.save_state(self.state_file, state)
        aws.tasks = [older]

        def describe_historical(task_id):
            return latest if task_id == TASK_LATEST else older

        with (
            mock.patch.object(aws, "describe_export", side_effect=describe_historical),
            self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
        ):
            self.run_refresh(aws)

        self.assertEqual(aws.synced, [])
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())

    def test_equal_timestamp_checkpoint_cannot_replace_different_target(self):
        aws = FakeAWS(self.settings)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        other = aws.task(TASK_OLDER, completed_at=LATEST_COMPLETED)
        aws.tasks = [latest, other]
        self.write_installed_state(aws, TASK_LATEST)
        self.write_active_state(other)
        aws.tasks = [other]

        def describe_historical(task_id):
            return latest if task_id == TASK_LATEST else other

        with (
            mock.patch.object(aws, "describe_export", side_effect=describe_historical),
            self.assertRaisesRegex(RuntimeError, "share a protected timestamp"),
        ):
            self.run_refresh(aws)

        self.assertEqual(aws.synced, [])
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())

    def test_stale_prepublication_checkpoint_is_abandoned_for_new_candidate(self):
        stale_completed = self.now - self.settings.max_export_age - timedelta(seconds=1)
        aws = FakeAWS(self.settings)
        stale = aws.task(TASK_PREVIOUS_WEEK, completed_at=stale_completed)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        aws.tasks = [stale, latest]
        staging = self.settings.staging_path(TASK_PREVIOUS_WEEK)
        staging.mkdir()
        (staging / "partial").write_text("discard")
        self.write_active_state(stale)

        result = self.run_refresh(aws)

        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertFalse(staging.exists())

    def test_stale_postswap_install_keeps_valid_published_target_while_replanning(
        self,
    ):
        stale_completed = self.now - self.settings.max_export_age - timedelta(seconds=1)
        aws = FakeAWS(self.settings)
        stale = aws.task(TASK_PREVIOUS_WEEK, completed_at=stale_completed)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        aws.tasks = [stale, latest]
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        staging = self.settings.staging_path(TASK_PREVIOUS_WEEK)
        aws.sync_export(TASK_PREVIOUS_WEEK, staging)
        manifest = self.checksum_manifest(aws, TASK_PREVIOUS_WEEK)
        exporter.atomic_exchange(self.target, staging)
        self.write_active_state(stale, phase="installing", sha256=manifest)
        aws.synced.clear()
        aws.sync_error = RuntimeError("new candidate download failed")

        with self.assertRaisesRegex(RuntimeError, "new candidate download failed"):
            self.run_refresh(aws)

        self.assertFalse((self.target / "current.txt").exists())
        self.assertTrue(
            (self.target / f"export_info_{TASK_PREVIOUS_WEEK}.json").is_file()
        )
        self.assertFalse(staging.exists())
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertEqual(
            json.loads(self.state_file.read_text())["task_id"], TASK_LATEST
        )

    def test_stale_in_progress_task_without_newer_candidate_fails_freshness(self):
        stale_completed = self.now - self.settings.max_export_age - timedelta(seconds=1)
        aws = FakeAWS(
            self.settings,
            tasks=[
                FakeAWS(self.settings).task(
                    TASK_PREVIOUS_WEEK, completed_at=stale_completed
                )
            ],
        )
        exporter.save_state(
            self.state_file,
            {
                "version": 2,
                "phase": "downloading",
                "task_id": TASK_PREVIOUS_WEEK,
                "task_timestamp": stale_completed.isoformat(),
                "source_arn": self.settings.source_arn,
                "s3_bucket": self.settings.s3_bucket,
                "export_only": list(self.settings.export_only),
                "iam_role_arn": self.settings.iam_role_arn,
                "kms_key_arn": self.settings.kms_key_arn,
            },
        )

        with self.assertRaisesRegex(RuntimeError, "older than"):
            self.run_refresh(aws)
        with self.assertRaisesRegex(RuntimeError, "older than"):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)

        self.assertEqual(aws.synced, [])
        self.assertEqual(aws.described, [])

    def test_expired_stale_checkpoint_replans_without_describing_missing_task(self):
        stale_completed = self.now - self.settings.max_export_age - timedelta(seconds=1)
        aws = FakeAWS(self.settings)
        stale = aws.task(TASK_PREVIOUS_WEEK, completed_at=stale_completed)
        latest = aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED)
        aws.tasks = [latest]
        self.write_active_state(stale)

        output = exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        self.assertIn(TASK_LATEST, output)
        self.assertEqual(aws.described, [])
        self.assertEqual(
            json.loads(self.state_file.read_text())["task_id"], TASK_PREVIOUS_WEEK
        )

        result = self.run_refresh(aws)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.described, [])

    def test_foreign_temporal_metadata_names_are_rejected_before_publication(self):
        self.target.mkdir()
        (self.target / "only-old-copy.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.foreign_metadata_name = True

        with self.assertRaisesRegex(
            RuntimeError, "outside requested export scopes|missing"
        ):
            self.run_refresh(aws)

        self.assertEqual((self.target / "only-old-copy.txt").read_text(), "keep")

    def test_exact_temporal_metadata_names_are_accepted(self):
        aws = FakeAWS(self.settings)
        result = self.run_refresh(aws)
        self.assertTrue(result.changed)
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertTrue(
            (
                self.target / f"export_tables_info_{TASK_LATEST}_from_1_to_2.json"
            ).is_file()
        )

    def test_atomic_exchange_swaps_directories_without_removing_either_path(self):
        left = Path(self.tempdir.name) / "left"
        right = Path(self.tempdir.name) / "right"
        left.mkdir()
        right.mkdir()
        (left / "left.txt").write_text("left")
        (right / "right.txt").write_text("right")
        exporter.atomic_exchange(left, right)
        self.assertEqual((left / "right.txt").read_text(), "right")
        self.assertEqual((right / "left.txt").read_text(), "left")

    def test_existing_target_publication_uses_atomic_exchange(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        real_exchange = exporter.atomic_exchange
        exchanges = []

        def record_exchange(left, right):
            self.assertTrue(self.target.is_dir())
            real_exchange(left, right)
            self.assertTrue(self.target.is_dir())
            exchanges.append((left, right))

        with mock.patch.object(
            exporter, "atomic_exchange", side_effect=record_exchange
        ):
            result = self.run_refresh(aws)
        self.assertTrue(result.changed)
        self.assertEqual(
            exchanges,
            [(self.target, self.settings.staging_path(TASK_LATEST))],
        )

    def test_state_write_failure_before_swap_preserves_current_target(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        real_save_state = exporter.save_state

        def fail_installing_state(path, state):
            if state.get("phase") == "installing":
                raise OSError("simulated installing checkpoint failure")
            return real_save_state(path, state)

        with (
            mock.patch.object(
                exporter, "save_state", side_effect=fail_installing_state
            ),
            self.assertRaisesRegex(OSError, "installing checkpoint failure"),
        ):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "downloaded")

    def test_crash_after_atomic_exchange_is_recovered_on_retry(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        real_exchange = exporter.atomic_exchange

        def exchange_then_crash(left, right):
            real_exchange(left, right)
            raise OSError("simulated crash after exchange")

        with (
            mock.patch.object(
                exporter, "atomic_exchange", side_effect=exchange_then_crash
            ),
            self.assertRaisesRegex(OSError, "crash after exchange"),
        ):
            self.run_refresh(aws)

        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertEqual(
            (self.settings.staging_path(TASK_LATEST) / "current.txt").read_text(),
            "old",
        )

        result = self.run_refresh(aws)
        self.assertTrue(result.changed)
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")
        self.assertFalse(self.settings.staging_path(TASK_LATEST).exists())

    def test_same_task_force_crash_after_exchange_recovers(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        real_exchange = exporter.atomic_exchange

        def exchange_then_crash(left, right):
            real_exchange(left, right)
            raise OSError("simulated same-task crash after exchange")

        with (
            mock.patch.object(
                exporter, "atomic_exchange", side_effect=exchange_then_crash
            ),
            self.assertRaisesRegex(OSError, "same-task crash after exchange"),
        ):
            self.run_refresh(aws, force=True)

        result = self.run_refresh(aws)
        self.assertTrue(result.changed)
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")
        self.assertFalse(self.settings.staging_path(TASK_LATEST).exists())
        self.assertFalse(self.settings.backup_path(TASK_LATEST).exists())

    def test_same_task_corrupt_staging_keeps_manifest_valid_target(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        staging = self.settings.staging_path(TASK_LATEST)
        aws.sync_export(TASK_LATEST, staging)
        next(staging.rglob("*.parquet")).write_bytes(b"corrupt")
        self.write_active_state(
            aws.tasks[0],
            phase="installing",
            sha256=self.checksum_manifest(aws, TASK_LATEST),
        )
        aws.synced.clear()

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [])
        self.assertFalse(staging.exists())
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")

    def test_same_task_crash_after_backup_normalization_recovers(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        real_save_state = exporter.save_state
        failed = False

        def fail_first_installed_state(path, state):
            nonlocal failed
            if state.get("phase") == "installed" and not failed:
                failed = True
                raise OSError("simulated crash after backup normalization")
            return real_save_state(path, state)

        with (
            mock.patch.object(
                exporter, "save_state", side_effect=fail_first_installed_state
            ),
            self.assertRaisesRegex(OSError, "backup normalization"),
        ):
            self.run_refresh(aws, force=True)

        self.assertTrue(self.settings.backup_path(TASK_LATEST).exists())
        result = self.run_refresh(aws)
        self.assertTrue(result.changed)
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")
        self.assertFalse(self.settings.backup_path(TASK_LATEST).exists())

    def test_dry_run_rejects_ambiguous_install_artifacts_without_mutation(self):
        import shutil

        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        staging = self.settings.staging_path(TASK_LATEST)
        backup = self.settings.backup_path(TASK_LATEST)
        shutil.copytree(self.target, staging)
        shutil.copytree(self.target, backup)
        self.write_active_state(
            aws.tasks[0],
            phase="installing",
            sha256=self.checksum_manifest(aws, TASK_LATEST),
        )

        with self.assertRaisesRegex(RuntimeError, "staging and backup present"):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)

        self.assertTrue(staging.exists())
        self.assertTrue(backup.exists())
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installing")

    def test_postpublication_cleanup_failure_keeps_new_target_and_retries_cleanup(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        backup = self.settings.backup_path(TASK_LATEST)
        real_rmtree = exporter.shutil.rmtree

        def fail_backup(path, *args, **kwargs):
            if Path(path) == backup:
                raise OSError("simulated publication cleanup failure")
            return real_rmtree(path, *args, **kwargs)

        with (
            mock.patch.object(exporter.shutil, "rmtree", side_effect=fail_backup),
            self.assertRaisesRegex(OSError, "publication cleanup failure"),
        ):
            self.run_refresh(aws)

        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertTrue(backup.exists())

        aws.synced.clear()
        result = self.run_refresh(aws)
        self.assertFalse(result.changed)
        self.assertFalse(backup.exists())
        self.assertEqual(aws.synced, [])

    def test_sync_failure_preserves_existing_directory(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings, sync_error=RuntimeError("sync failed"))
        with self.assertRaisesRegex(RuntimeError, "sync failed"):
            self.run_refresh(aws)
        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(
            json.loads(self.state_file.read_text())["phase"], "downloading"
        )

    def test_inventory_and_metadata_integrity_fail_before_publication(self):
        cases = (
            ("omit_checksum", True, "does not expose an S3 checksum"),
            ("warning_message", "warning", "completed with a warning"),
            ("table_status", "FAILED", "table metadata is incomplete"),
            ("extra_scope_object", True, "outside requested export scopes"),
            ("extra_table_target", True, "table target outside export scopes"),
            ("nested_metadata_key", True, "unexpected table metadata key"),
            ("malformed_data_key", True, "unexpected export data key"),
            ("missing_success", True, "missing _SUCCESS"),
            ("partition_without_success", True, "missing _SUCCESS"),
            ("unlisted_data_table", True, "has no exact table metadata"),
            (
                "omit_reference_partition",
                True,
                "has no export data or _SUCCESS",
            ),
            (
                "public_metadata_target",
                "postgres.public.different",
                "has no exact table metadata",
            ),
        )
        for attribute, value, message in cases:
            with (
                self.subTest(attribute=attribute),
                tempfile.TemporaryDirectory() as root,
            ):
                settings = exporter.Settings(
                    target=Path(root) / "production_db",
                    state_file=Path(root) / "state.json",
                    lock_file=Path(root) / "lock",
                )
                settings.target.mkdir()
                (settings.target / "current.txt").write_text("keep")
                aws = FakeAWS(settings)
                if attribute == "warning_message":
                    aws.tasks[0]["WarningMessage"] = value
                else:
                    setattr(aws, attribute, value)
                with self.assertRaisesRegex(RuntimeError, message):
                    exporter.refresh_once(settings, aws, clock=lambda: self.now)
                self.assertEqual(aws.synced, [])
                self.assertEqual((settings.target / "current.txt").read_text(), "keep")

    def test_completed_metadata_supports_empty_tables_with_success_markers(self):
        aws = FakeAWS(self.settings)
        aws.all_tables_empty = True

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertFalse(any(self.target.rglob("*.parquet")))

    def test_success_only_empty_partition_does_not_require_parquet(self):
        aws = FakeAWS(self.settings)
        aws.omit_parquet = True

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertTrue(next(self.target.rglob("_SUCCESS")).is_file())
        self.assertFalse(any(self.target.rglob("*.parquet")))

    def test_same_size_corrupt_resumed_file_is_not_reused(self):
        aws = FakeAWS(self.settings)
        staging = self.settings.staging_path(TASK_LATEST)
        aws.sync_export(TASK_LATEST, staging)
        aws.synced.clear()
        manifest = self.checksum_manifest(aws, TASK_LATEST)
        parquet = next(staging.rglob("*.parquet"))
        parquet.write_bytes(b"BAD!test")
        exporter.save_state(
            self.state_file,
            {
                "version": 2,
                "phase": "downloaded",
                "task_id": TASK_LATEST,
                "task_timestamp": LATEST_COMPLETED.isoformat(),
                "sha256": manifest,
                "source_arn": self.settings.source_arn,
                "s3_bucket": self.settings.s3_bucket,
                "export_only": list(self.settings.export_only),
                "iam_role_arn": self.settings.iam_role_arn,
                "kms_key_arn": self.settings.kms_key_arn,
            },
        )

        def skip_same_size(task_id, destination):
            aws.synced.append(task_id)
            prefix = f"{task_id}/"
            for key, value in aws._objects(task_id).items():
                path = destination / key.removeprefix(prefix)
                if path.is_file() and path.stat().st_size == len(value):
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)

        with mock.patch.object(aws, "sync_export", side_effect=skip_same_size):
            self.run_refresh(aws)
        self.assertEqual(aws.list_calls, 0)
        self.assertEqual(aws.described, [TASK_LATEST])
        self.assertEqual(next(self.target.rglob("*.parquet")).read_bytes(), b"PAR1test")

    def test_disk_check_requires_complete_incoming_export_plus_headroom(self):
        aws = FakeAWS(self.settings)
        inventory = exporter.build_inventory(
            TASK_LATEST,
            aws.list_export_objects(TASK_LATEST),
            self.settings.export_only,
        )
        self.settings.free_space_headroom_bytes = 10
        with (
            mock.patch.object(
                exporter.shutil,
                "disk_usage",
                return_value=mock.Mock(free=inventory.total_bytes + 9),
            ),
            self.assertRaisesRegex(RuntimeError, "not enough free disk"),
        ):
            self.run_refresh(aws)
        self.assertEqual(aws.synced, [])

    def test_dry_run_is_read_only_and_reports_latest_migration_or_noop(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old")
        exporter.save_state(
            self.state_file,
            {"version": 1, "phase": "installed", "task_id": LEGACY_TASK},
        )
        aws = FakeAWS(self.settings)
        before_state = self.state_file.read_bytes()

        report = exporter.dry_run(self.settings, aws, clock=lambda: self.now)

        self.assertIn(TASK_LATEST, report)
        self.assertIn("migrate", report.lower())
        self.assertEqual(self.state_file.read_bytes(), before_state)
        self.assertEqual(aws.synced, [])

        self.write_installed_state(aws)
        report = exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        self.assertIn("no-op", report.lower())
        self.assertIn(TASK_LATEST, report)

    def test_refuses_to_downgrade_when_installed_provenance_is_newer_than_listing(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        latest = aws.tasks[1]
        older = aws.tasks[0]
        self.write_installed_state(aws, TASK_LATEST)
        aws.tasks = [older]

        def describe_historical(task_id):
            aws.described.append(task_id)
            return latest if task_id == TASK_LATEST else older

        with (
            mock.patch.object(aws, "describe_export", side_effect=describe_historical),
            self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
        ):
            self.run_refresh(aws)
        with (
            mock.patch.object(aws, "describe_export", side_effect=describe_historical),
            self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
        ):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)

        self.assertEqual(aws.synced, [])
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())

    def test_dry_run_does_not_resume_checkpoint_older_than_declared_target(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_LATEST)
        self.write_active_state(aws.tasks[0])
        before_target = {
            path.relative_to(self.target): path.read_bytes()
            for path in self.target.rglob("*")
            if path.is_file()
        }
        before_state = self.state_file.read_bytes()

        report = exporter.dry_run(self.settings, aws, clock=lambda: self.now)

        self.assertIn(TASK_LATEST, report)
        self.assertNotIn(f"resume selected follower task {TASK_OLDER}", report)
        self.assertEqual(self.state_file.read_bytes(), before_state)
        self.assertEqual(
            {
                path.relative_to(self.target): path.read_bytes()
                for path in self.target.rglob("*")
                if path.is_file()
            },
            before_target,
        )

    def test_declared_target_blocks_replayed_or_rejected_state_downgrade(self):
        aws = FakeAWS(self.settings)
        aws.tasks = [
            aws.task(TASK_OLDER, completed_at=OLDER_COMPLETED),
            aws.task(TASK_LATEST, completed_at=LATEST_COMPLETED),
        ]
        self.write_installed_state(aws, TASK_LATEST)
        latest = aws.tasks[1]
        older = aws.tasks[0]
        aws.tasks = [older]

        def describe_historical(task_id):
            aws.described.append(task_id)
            return latest if task_id == TASK_LATEST else older

        for phase in ("installed", "rejected"):
            with self.subTest(phase=phase):
                self.write_active_state(older, phase=phase)
                with (
                    mock.patch.object(
                        aws, "describe_export", side_effect=describe_historical
                    ),
                    self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
                ):
                    exporter.dry_run(self.settings, aws, clock=lambda: self.now)
                with (
                    mock.patch.object(
                        aws, "describe_export", side_effect=describe_historical
                    ),
                    self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
                ):
                    self.run_refresh(aws)
                self.assertTrue(
                    (self.target / f"export_info_{TASK_LATEST}.json").is_file()
                )
        self.state_file.unlink()
        with (
            mock.patch.object(aws, "describe_export", side_effect=describe_historical),
            self.assertRaisesRegex(RuntimeError, "refusing a downgrade"),
        ):
            self.run_refresh(aws)

    def test_postswap_recovery_finishes_without_describing_expired_predecessor(self):
        aws = FakeAWS(self.settings)
        self.target.mkdir()
        (self.target / "expired-predecessor.txt").write_text("old")
        staging = self.settings.staging_path(TASK_LATEST)
        aws.sync_export(TASK_LATEST, staging)
        manifest = self.checksum_manifest(aws, TASK_LATEST)
        exporter.atomic_exchange(self.target, staging)
        self.write_active_state(aws.tasks[0], phase="installing", sha256=manifest)
        aws.synced.clear()

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [])
        self.assertEqual(aws.described, [TASK_LATEST])
        self.assertFalse((self.target / "expired-predecessor.txt").exists())
        self.assertFalse(staging.exists())

    def test_partial_duplicate_cleanup_residue_never_replaces_valid_target(self):
        aws = FakeAWS(self.settings)
        self.write_installed_state(aws)
        manifest = self.checksum_manifest(aws, TASK_LATEST)
        staging = self.settings.staging_path(TASK_LATEST)
        staging.mkdir()
        (staging / "partial-after-rmtree").write_text("invalid residue")
        self.write_active_state(aws.tasks[0], phase="installing", sha256=manifest)

        aws.describe_error = RuntimeError("injected describe failure")
        with self.assertRaisesRegex(RuntimeError, "injected describe failure"):
            self.run_refresh(aws)
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertEqual(
            (staging / "partial-after-rmtree").read_text(), "invalid residue"
        )

        aws.describe_error = None
        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertTrue((self.target / f"export_info_{TASK_LATEST}.json").is_file())
        self.assertFalse((self.target / "partial-after-rmtree").exists())
        self.assertFalse(staging.exists())

    def test_downloading_checkpoint_unsafe_staging_fails_in_dry_run_and_execution(self):
        aws = FakeAWS(self.settings)
        self.write_active_state(aws.tasks[0], phase="downloading")
        staging = self.settings.staging_path(TASK_LATEST)
        staging.write_text("not a directory")

        with self.assertRaisesRegex(RuntimeError, "unsafe staging path"):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        with self.assertRaisesRegex(RuntimeError, "unsafe staging path"):
            self.run_refresh(aws)
        self.assertEqual(staging.read_text(), "not a directory")
        self.assertEqual(aws.synced, [])

    def test_dry_run_enforces_remote_inventory_and_metadata_gates(self):
        for attribute, expected in (
            ("omit_checksum", "does not expose an S3 checksum"),
            ("missing_success", "missing _SUCCESS"),
            ("table_status", "table metadata is incomplete"),
        ):
            with self.subTest(attribute=attribute):
                aws = FakeAWS(self.settings)
                setattr(
                    aws, attribute, "FAILED" if attribute == "table_status" else True
                )
                with self.assertRaisesRegex(RuntimeError, expected):
                    exporter.dry_run(self.settings, aws, clock=lambda: self.now)
                self.assertEqual(aws.synced, [])

    def test_export_info_provenance_fields_are_pinned(self):
        cases = {
            "sourceArn": "arn:aws:rds:us-east-1:000000000000:cluster:foreign",
            "exportOnly": ["postgres.public", "postgres.private"],
            "s3Bucket": "foreign-bucket",
            "s3Prefix": "foreign-prefix",
            "exportedFilesPath": TASK_OLDER,
            "iamRoleArn": "arn:aws:iam::000000000000:role/foreign",
            "kmsKeyId": "arn:aws:kms:us-east-1:000000000000:key/foreign",
            "percentProgress": 99,
            "taskStartTime": "2026-08-16T10:00:00+00:00",
            "taskEndTime": "2026-08-16T12:30:00+00:00",
            "totalExportedDataInGB": 999.0,
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                aws = FakeAWS(self.settings)
                aws.export_info_changes[field] = value
                with self.assertRaisesRegex(
                    RuntimeError,
                    "wrong export scopes"
                    if field == "exportOnly"
                    else f"wrong {field}",
                ):
                    exporter.dry_run(self.settings, aws, clock=lambda: self.now)
                self.assertEqual(aws.synced, [])

        aws = FakeAWS(self.settings)
        aws.export_info_changes["percentProgress"] = 100.0
        with self.assertRaisesRegex(RuntimeError, "wrong percentProgress"):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)

    def test_rds_task_provenance_fields_are_type_strict(self):
        cases = {
            "ExportOnly": {
                "postgres.public": True,
                "postgres.reference": True,
            },
            "S3Prefix": False,
            "PercentProgress": "100",
            "TotalExtractedDataInGB": "0",
            "TaskStartTime": {"not": "a timestamp"},
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                task = FakeAWS(self.settings).task(**{field: value})
                with self.assertRaisesRegex(
                    RuntimeError,
                    "task timestamps" if field == "TaskStartTime" else field,
                ):
                    exporter.validate_completed_task(self.settings, TASK_LATEST, task)

    def test_prior_installed_evidence_survives_new_candidate_preflight_failure(self):
        aws = FakeAWS(self.settings)
        previous = aws.task(TASK_PREVIOUS_WEEK)
        latest = aws.task(TASK_LATEST)
        aws.tasks = [previous, latest]
        self.write_installed_state(aws, TASK_PREVIOUS_WEEK)

        original_list_objects = aws.list_export_objects

        def fail_inventory(task_id):
            raise exporter.AWSCommandError(f"injected inventory failure for {task_id}")

        aws.list_export_objects = fail_inventory
        with self.assertRaisesRegex(RuntimeError, "injected inventory failure"):
            self.run_refresh(aws)
        failed_state = json.loads(self.settings.state_file.read_text())
        self.assertEqual(failed_state["phase"], "complete")
        self.assertEqual(
            failed_state["installed_target"]["task_id"], TASK_PREVIOUS_WEEK
        )
        self.assertEqual(
            exporter.declared_export_task_id(self.settings.target), TASK_PREVIOUS_WEEK
        )

        aws.tasks = [latest]
        aws.list_export_objects = original_list_objects
        report = exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        self.assertIn(TASK_LATEST, report)
        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertNotIn(TASK_PREVIOUS_WEEK, aws.described)
        installed_state = json.loads(self.settings.state_file.read_text())
        self.assertNotIn("installed_target", installed_state)

    def test_trusted_installed_snapshot_advances_after_old_rds_task_expires(self):
        aws = FakeAWS(self.settings)
        previous = aws.task(TASK_PREVIOUS_WEEK)
        latest = aws.task(TASK_LATEST)
        aws.tasks = [previous, latest]
        self.write_installed_state(aws, TASK_PREVIOUS_WEEK)
        aws.tasks = [latest]

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, TASK_LATEST)
        self.assertEqual(aws.synced, [TASK_LATEST])
        self.assertNotIn(TASK_PREVIOUS_WEEK, aws.described)

    def test_dry_run_checks_capacity_only_when_a_download_is_required(self):
        aws = FakeAWS(self.settings)
        with (
            mock.patch.object(
                exporter.shutil,
                "disk_usage",
                return_value=mock.Mock(free=0),
            ),
            self.assertRaisesRegex(RuntimeError, "not enough free disk"),
        ):
            exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        self.assertEqual(aws.synced, [])

        self.write_installed_state(aws)
        with mock.patch.object(
            exporter.shutil,
            "disk_usage",
            return_value=mock.Mock(free=0),
        ):
            report = exporter.dry_run(self.settings, aws, clock=lambda: self.now)
        self.assertIn("no-op", report.lower())

    def test_inventory_key_grammar_rejects_unicode_decimal_digits(self):
        self.assertFalse(
            exporter.is_allowed_export_data_key(
                "postgres/public.example/١/_SUCCESS", self.settings.export_only
            )
        )
        with self.assertRaisesRegex(RuntimeError, "unexpected table metadata key"):
            exporter.validate_inventory_names(
                TASK_LATEST,
                {
                    f"export_info_{TASK_LATEST}.json",
                    f"export_tables_info_{TASK_LATEST}_from_١_to_2.json",
                },
                self.settings.export_only,
            )
        for filename in ("part-💣.parquet", "part-line\nbreak.parquet"):
            with self.subTest(filename=filename):
                self.assertFalse(
                    exporter.is_allowed_export_data_key(
                        f"postgres/public.example/1/{filename}",
                        self.settings.export_only,
                    )
                )

    def test_main_dry_run_does_not_create_lock_state_or_target(self):
        aws = FakeAWS(self.settings)
        stdout = io.StringIO()
        with (
            mock.patch.object(exporter, "Settings", return_value=self.settings),
            mock.patch.object(exporter, "AWSClient", return_value=aws),
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(exporter.main(["--dry-run"]), 0)

        self.assertIn(TASK_LATEST, stdout.getvalue())
        self.assertFalse(self.settings.lock_file.exists())
        self.assertFalse(self.settings.state_file.exists())
        self.assertFalse(self.settings.target.exists())

    def test_successful_main_run_is_silent_and_failure_is_nonzero(self):
        aws = FakeAWS(self.settings)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(exporter, "Settings", return_value=self.settings),
            mock.patch.object(exporter, "AWSClient", return_value=aws),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(exporter.main([]), 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

        bad = FakeAWS(
            self.settings,
            identity_arn=f"arn:aws:sts::{self.settings.account_id}:assumed-role/Admin/x",
        )
        stderr = io.StringIO()
        with (
            mock.patch.object(exporter, "Settings", return_value=self.settings),
            mock.patch.object(exporter, "AWSClient", return_value=bad),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(exporter.main([]), 1)
        self.assertIn("Weekly production DB follower failed", stderr.getvalue())

    def test_s3_download_enables_checksum_validation(self):
        client = exporter.AWSClient(self.settings, binary="/usr/bin/aws")
        completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with mock.patch.object(
            exporter.subprocess, "run", return_value=completed
        ) as run:
            client.sync_export(TASK_LATEST, self.target)
        command = run.call_args.args[0]
        checksum_option = command.index("--checksum-mode")
        self.assertEqual(command[checksum_option + 1], "ENABLED")


if __name__ == "__main__":
    unittest.main()
