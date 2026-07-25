from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
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


class FakeAWS:
    def __init__(
        self, settings, *, account_id=None, sync_error=None, omit_parquet=False
    ):
        self.settings = settings
        self.account_id = account_id or settings.account_id
        self.sync_error = sync_error
        self.omit_parquet = omit_parquet
        self.started = []
        self.synced = []
        self.known_tasks = set()
        self.expired_object_tasks = set()
        self.list_error: Exception | None = None
        self.warning_message: str | None = None
        self.table_status = "COMPLETE"
        self.omit_checksum = False
        self.extra_scope_object = False
        self.extra_table_target = False
        self.nested_metadata_key = False
        self.malformed_data_key = False

    def get_identity(self):
        return {
            "Account": self.account_id,
            "Arn": f"arn:aws:sts::{self.account_id}:assumed-role/HermesAgentReadOnly/test",
        }

    def start_export(self, task_id):
        self.started.append(task_id)
        self.known_tasks.add(task_id)
        return self._task(task_id)

    def describe_export(self, task_id):
        if task_id not in self.known_tasks:
            return None
        return self._task(task_id)

    def list_export_objects(self, task_id):
        if self.list_error is not None:
            raise self.list_error
        if task_id in self.expired_object_tasks:
            return []
        result = []
        for key, value in self._objects(task_id).items():
            item = {"Key": key, "Size": len(value)}
            if not self.omit_checksum:
                item["ChecksumAlgorithm"] = ["CRC64NVME"]
            result.append(item)
        return result

    def sync_export(self, task_id, destination):
        self.synced.append(task_id)
        if self.sync_error:
            raise self.sync_error
        prefix = f"{task_id}/"
        destination.mkdir(parents=True, exist_ok=True)
        for key, value in self._objects(task_id).items():
            relative = key.removeprefix(prefix)
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)

    def _task(self, task_id):
        return {
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
        }

    def _objects(self, task_id):
        prefix = f"{task_id}/"
        table_statuses = [
            {
                "target": "postgres.public.example",
                "status": self.table_status,
            },
            {
                "target": "postgres.reference.example",
                "status": "COMPLETE",
            },
        ]
        if self.extra_table_target:
            table_statuses.append(
                {"target": "postgres.private.secret", "status": "COMPLETE"}
            )
        objects = {
            prefix + f"export_info_{task_id}.json": json.dumps(
                {
                    "exportTaskIdentifier": task_id,
                    "status": "COMPLETE",
                    "exportedFilesPath": task_id,
                }
            ).encode(),
            prefix + f"export_tables_info_{task_id}_from_1_to_2.json": json.dumps(
                {"perTableStatus": table_statuses}
            ).encode(),
            prefix + "postgres/public.example/1/_SUCCESS": b"",
        }
        if not self.omit_parquet:
            objects[prefix + "postgres/public.example/1/part-00000.gz.parquet"] = (
                b"PAR1test"
            )
        if self.extra_scope_object:
            objects[prefix + "postgres/private.secret/1/part-00000.gz.parquet"] = (
                b"PAR1secret"
            )
        if self.nested_metadata_key:
            objects[
                prefix + f"export_tables_info_{task_id}_shadow/postgres/private.json"
            ] = b"not parsed or scoped"
        if self.malformed_data_key:
            objects[prefix + "postgres/public.example/1/not-parquet.txt"] = b"invalid"
        return objects


class WeeklyProductionDBExportTests(unittest.TestCase):
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
            min_interval=timedelta(days=6),
        )
        self.now = datetime(2026, 7, 24, 18, 0, tzinfo=timezone.utc)

    def run_refresh(self, aws, *, force=False):
        return exporter.refresh_once(
            self.settings,
            aws,
            force=force,
            clock=lambda: self.now,
            sleeper=lambda _: None,
        )

    @staticmethod
    def checksum_manifest(aws, task_id):
        prefix = f"{task_id}/"
        return {
            key.removeprefix(prefix): hashlib.sha256(value).hexdigest()
            for key, value in aws._objects(task_id).items()
        }

    def test_managed_cron_job_excludes_mutable_runtime_state(self):
        payload = json.loads(CRON_JOBS.read_text())
        job = next(job for job in payload["jobs"] if job["id"] == "74cd4bc9ba5d")

        self.assertEqual(job["repeat"], {"times": None})
        for key in (
            "next_run_at",
            "last_run_at",
            "last_status",
            "last_error",
            "last_delivery_error",
            "fire_claim",
        ):
            self.assertNotIn(key, job)

    def test_atomic_exchange_swaps_directories_without_removing_either_path(self):
        left = Path(self.tempdir.name) / "left"
        right = Path(self.tempdir.name) / "right"
        left.mkdir()
        right.mkdir()
        (left / "left.txt").write_text("left")
        (right / "right.txt").write_text("right")

        exporter.atomic_exchange(left, right)

        self.assertTrue(left.is_dir())
        self.assertTrue(right.is_dir())
        self.assertEqual((left / "right.txt").read_text(), "right")
        self.assertEqual((right / "left.txt").read_text(), "left")

    def test_replaces_existing_directory_only_after_valid_download(self):
        (self.target / "analysis").mkdir(parents=True)
        (self.target / "analysis" / "old.txt").write_text("old")
        aws = FakeAWS(self.settings)

        result = self.run_refresh(aws)

        expected_task = "transformity-production-no-audit-scraper-20260724-180000"
        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, expected_task)
        self.assertEqual(aws.started, [expected_task])
        self.assertEqual(aws.synced, [expected_task])
        self.assertFalse((self.target / "analysis" / "old.txt").exists())
        self.assertEqual(
            (
                self.target
                / "postgres"
                / "public.example"
                / "1"
                / "part-00000.gz.parquet"
            ).read_bytes(),
            b"PAR1test",
        )
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "installed")
        self.assertEqual(state["task_id"], expected_task)
        self.assertFalse(self.settings.staging_path(expected_task).exists())
        self.assertFalse(self.settings.backup_path(expected_task).exists())

    def test_existing_target_is_published_with_atomic_exchange(self):
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
        self.assertEqual(len(exchanges), 1)
        self.assertEqual(exchanges[0][0], self.target)
        self.assertEqual(exchanges[0][1], self.settings.staging_path(result.task_id))

    def test_recovers_if_interrupted_immediately_after_atomic_exchange(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        task_id = "transformity-production-no-audit-scraper-20260724-180000"
        staging = self.settings.staging_path(task_id)
        backup = self.settings.backup_path(task_id)
        real_rename = Path.rename

        def interrupt_old_snapshot_rename(path, destination):
            if path == staging and Path(destination) == backup:
                raise OSError("simulated interruption after exchange")
            return real_rename(path, destination)

        with (
            mock.patch.object(
                Path, "rename", autospec=True, side_effect=interrupt_old_snapshot_rename
            ),
            self.assertRaisesRegex(OSError, "simulated interruption after exchange"),
        ):
            self.run_refresh(aws)

        self.assertTrue(self.target.is_dir())
        self.assertTrue((self.target / f"export_info_{task_id}.json").is_file())
        self.assertEqual((staging / "current.txt").read_text(), "old")
        self.assertFalse(backup.exists())

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertFalse(staging.exists())
        self.assertFalse(backup.exists())
        self.assertEqual(aws.synced, [task_id])

    def test_recovers_if_interrupted_during_atomic_rollback(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installing",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        backup = self.settings.backup_path(task_id)
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, backup)
        aws.synced.clear()

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [task_id])
        self.assertTrue((self.target / f"export_info_{task_id}.json").is_file())
        self.assertFalse(backup.exists())
        self.assertFalse(self.settings.staging_path(task_id).exists())

    def test_installing_phase_survives_interruption_before_finish_install(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        aws.synced.clear()
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installing",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        backup = self.settings.backup_path(task_id)
        backup.mkdir()
        (backup / "old.txt").write_text("old")

        with (
            mock.patch.object(
                exporter,
                "finish_install",
                side_effect=OSError("simulated interruption before finish"),
            ),
            self.assertRaisesRegex(OSError, "simulated interruption before finish"),
        ):
            self.run_refresh(aws)

        interrupted = json.loads(self.state_file.read_text())
        self.assertEqual(interrupted["phase"], "installing")
        self.assertTrue(backup.is_dir())

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, task_id)
        self.assertFalse(backup.exists())
        self.assertFalse(self.settings.staging_path(task_id).exists())
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")

    def test_transient_inventory_error_preserves_installing_checkpoint(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        aws.synced.clear()
        staging = self.settings.staging_path(task_id)
        staging.mkdir()
        (staging / "old.txt").write_text("old")
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installing",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        aws.list_error = exporter.AWSCommandError("transient inventory failure")

        with self.assertRaisesRegex(
            exporter.AWSCommandError, "transient inventory failure"
        ):
            self.run_refresh(aws)

        interrupted = json.loads(self.state_file.read_text())
        self.assertEqual(interrupted["phase"], "installing")
        self.assertEqual((staging / "old.txt").read_text(), "old")

        aws.list_error = None
        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, task_id)
        self.assertEqual(aws.started, [])
        self.assertFalse(staging.exists())
        self.assertFalse(self.settings.backup_path(task_id).exists())
        self.assertEqual(json.loads(self.state_file.read_text())["phase"], "installed")

    def test_recent_success_is_idempotent(self):
        task_id = "transformity-production-no-audit-scraper-20260723-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": task_id,
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        aws.synced.clear()

        result = self.run_refresh(aws)

        self.assertFalse(result.changed)
        self.assertEqual(result.task_id, task_id)
        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [])
        self.assertTrue((self.target / f"export_info_{task_id}.json").is_file())
        state = json.loads(self.state_file.read_text())
        self.assertEqual(
            set(state["sha256"]),
            {key.removeprefix(f"{task_id}/") for key in aws._objects(task_id)},
        )

    def test_installed_state_without_manifest_fails_closed(self):
        task_id = "transformity-production-no-audit-scraper-20260723-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": task_id,
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
            },
        )
        aws.synced.clear()

        with self.assertRaisesRegex(RuntimeError, "trusted local SHA-256 manifest"):
            self.run_refresh(aws)

        state = json.loads(self.state_file.read_text())
        self.assertNotIn("sha256", state)
        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [])

    def test_recent_success_validates_target_even_without_a_cleanup_backup(self):
        task_id = "transformity-production-no-audit-scraper-20260723-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": task_id,
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )

        with self.assertRaisesRegex(RuntimeError, "download directory is missing"):
            self.run_refresh(aws)

        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [])

    def test_recent_install_detects_same_size_local_corruption(self):
        task_id = "transformity-production-no-audit-scraper-20260723-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        prefix = f"{task_id}/"
        checksums = {
            key.removeprefix(prefix): hashlib.sha256(value).hexdigest()
            for key, value in aws._objects(task_id).items()
        }
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": task_id,
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
                "sha256": checksums,
            },
        )
        parquet = next(self.target.rglob("*.parquet"))
        parquet.write_bytes(b"BAD!test")

        with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
            self.run_refresh(aws)

        self.assertEqual(parquet.read_bytes(), b"BAD!test")

    def test_resumes_a_started_task_without_creating_a_duplicate(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "waiting",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, task_id)
        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [task_id])

    def test_complete_staging_is_checksum_synced_before_install(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "downloading",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        staging = self.settings.staging_path(task_id)
        aws.sync_export(task_id, staging)
        aws.synced.clear()
        parquet = next(staging.rglob("*.parquet"))
        parquet.write_bytes(b"BAD!test")

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [task_id])
        installed_parquet = next(self.target.rglob("*.parquet"))
        self.assertEqual(installed_parquet.read_bytes(), b"PAR1test")
        self.assertFalse((self.target / "current.txt").exists())

    def test_resume_repairs_corruption_even_if_sync_skips_same_size_files(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        staging = self.settings.staging_path(task_id)
        aws.sync_export(task_id, staging)
        aws.synced.clear()
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "downloaded",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        parquet = next(staging.rglob("*.parquet"))
        parquet.write_bytes(b"BAD!test")

        def skip_existing_same_size(task, destination):
            aws.synced.append(task)
            prefix = f"{task}/"
            destination.mkdir(parents=True, exist_ok=True)
            for key, value in aws._objects(task).items():
                path = destination / key.removeprefix(prefix)
                if path.is_file() and path.stat().st_size == len(value):
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)

        with mock.patch.object(aws, "sync_export", side_effect=skip_existing_same_size):
            result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [task_id])
        installed_parquet = next(self.target.rglob("*.parquet"))
        self.assertEqual(installed_parquet.read_bytes(), b"PAR1test")
        self.assertFalse((self.target / "current.txt").exists())

    def test_resume_rejects_wrong_bytes_written_after_manifest_precheck(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        staging = self.settings.staging_path(task_id)
        aws.sync_export(task_id, staging)
        aws.synced.clear()
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "downloaded",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )

        def write_wrong_same_size_bytes(task, destination):
            aws.synced.append(task)
            prefix = f"{task}/"
            for key, value in aws._objects(task).items():
                path = destination / key.removeprefix(prefix)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"BAD!test" if key.endswith(".parquet") else value)

        with (
            mock.patch.object(
                aws, "sync_export", side_effect=write_wrong_same_size_bytes
            ),
            mock.patch.object(exporter, "atomic_exchange") as exchange,
            self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"),
        ):
            self.run_refresh(aws)

        exchange.assert_not_called()
        self.assertEqual((self.target / "current.txt").read_text(), "old")
        self.assertEqual(next(staging.rglob("*.parquet")).read_bytes(), b"BAD!test")
        self.assertEqual(
            json.loads(self.state_file.read_text())["phase"], "downloading"
        )

    def test_resume_without_manifest_retransfers_complete_files(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        staging = self.settings.staging_path(task_id)
        aws.sync_export(task_id, staging)
        aws.synced.clear()
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "downloading",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        parquet = next(staging.rglob("*.parquet"))
        parquet.write_bytes(b"BAD!test")

        def skip_existing_same_size(task, destination):
            aws.synced.append(task)
            prefix = f"{task}/"
            destination.mkdir(parents=True, exist_ok=True)
            for key, value in aws._objects(task).items():
                path = destination / key.removeprefix(prefix)
                if path.is_file() and path.stat().st_size == len(value):
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)

        with mock.patch.object(aws, "sync_export", side_effect=skip_existing_same_size):
            result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(aws.synced, [task_id])
        installed_parquet = next(self.target.rglob("*.parquet"))
        self.assertEqual(installed_parquet.read_bytes(), b"PAR1test")
        self.assertFalse((self.target / "current.txt").exists())

    def test_download_space_requires_full_incoming_capacity_with_reusable_files(
        self,
    ):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        objects = aws._objects(task_id)
        inventory = exporter.build_inventory(
            task_id, aws.list_export_objects(task_id), self.settings.export_only
        )
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "downloading",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        prefix = f"{task_id}/"
        first_key, first_value = next(iter(objects.items()))
        relative = first_key.removeprefix(prefix)
        partial = self.settings.staging_path(task_id) / relative
        partial.parent.mkdir(parents=True)
        partial.write_bytes(first_value)
        self.settings.free_space_headroom_bytes = 10
        insufficient_free = inventory.total_bytes + 9

        with (
            mock.patch.object(
                exporter.shutil,
                "disk_usage",
                return_value=mock.Mock(free=insufficient_free),
            ),
            self.assertRaisesRegex(RuntimeError, "not enough free disk"),
        ):
            self.run_refresh(aws)

        self.assertEqual(aws.synced, [])

    def test_finishes_cleanup_after_a_crash_following_the_directory_swap(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installing",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        aws.synced.clear()
        backup = self.settings.backup_path(task_id)
        backup.mkdir()
        (backup / "old.txt").write_text("old")

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, task_id)
        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [task_id])
        self.assertFalse(backup.exists())
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "installed")

    def test_restores_old_snapshot_before_resuming_an_interrupted_install(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installing",
                "task_id": task_id,
                "started_at": self.now.isoformat(),
            },
        )
        backup = self.settings.backup_path(task_id)
        backup.mkdir()
        (backup / "current.txt").write_text("old")
        aws = FakeAWS(
            self.settings, sync_error=RuntimeError("simulated resume sync failure")
        )
        aws.known_tasks.add(task_id)

        with self.assertRaisesRegex(RuntimeError, "simulated resume sync failure"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "old")
        self.assertFalse(backup.exists())

    def test_cleanup_failure_never_restores_a_partially_deleted_old_snapshot(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("old")
        aws = FakeAWS(self.settings)
        real_rmtree = exporter.shutil.rmtree
        expected_task = "transformity-production-no-audit-scraper-20260724-180000"
        backup = self.settings.backup_path(expected_task)

        def partially_delete_then_fail(path):
            path = Path(path)
            if path == backup:
                (path / "current.txt").unlink()
                raise OSError("simulated backup cleanup failure")
            return real_rmtree(path)

        with (
            mock.patch.object(
                exporter.shutil, "rmtree", side_effect=partially_delete_then_fail
            ),
            self.assertRaisesRegex(OSError, "simulated backup cleanup failure"),
        ):
            self.run_refresh(aws)

        metadata = self.target / f"export_info_{expected_task}.json"
        self.assertTrue(metadata.is_file())
        self.assertFalse((self.target / "current.txt").exists())
        self.assertTrue(backup.is_dir())
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "installed")

        result = self.run_refresh(aws)

        self.assertFalse(result.changed)
        self.assertFalse(backup.exists())
        self.assertEqual(aws.started, [expected_task])
        self.assertEqual(aws.synced, [expected_task])

    def test_expired_install_cleans_old_backup_before_starting_next_export(self):
        installed_task = "transformity-production-no-audit-scraper-20260717-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(installed_task)
        aws.sync_export(installed_task, self.target)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": installed_task,
                "installed_at": (self.now - timedelta(days=7)).isoformat(),
                "sha256": self.checksum_manifest(aws, installed_task),
            },
        )
        aws.synced.clear()
        backup = self.settings.backup_path(installed_task)
        backup.mkdir()
        (backup / "old.txt").write_text("old")

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertFalse(backup.exists())
        self.assertEqual(
            aws.started,
            ["transformity-production-no-audit-scraper-20260724-180000"],
        )

    def test_expired_install_refreshes_after_source_objects_expire(self):
        installed_task = "transformity-production-no-audit-scraper-20260617-180000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(installed_task)
        aws.sync_export(installed_task, self.target)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": installed_task,
                "installed_at": (self.now - timedelta(days=37)).isoformat(),
                "sha256": self.checksum_manifest(aws, installed_task),
            },
        )
        aws.synced.clear()
        aws.expired_object_tasks.add(installed_task)

        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertEqual(
            aws.started,
            ["transformity-production-no-audit-scraper-20260724-180000"],
        )
        self.assertEqual(
            json.loads(self.state_file.read_text())["task_id"], result.task_id
        )

    def test_cleanup_retry_preserves_backup_when_installed_target_is_invalid(self):
        task_id = "transformity-production-no-audit-scraper-20260724-170000"
        aws = FakeAWS(self.settings)
        aws.known_tasks.add(task_id)
        aws.sync_export(task_id, self.target)
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": task_id,
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
                "sha256": self.checksum_manifest(aws, task_id),
            },
        )
        parquet = next(self.target.rglob("*.parquet"))
        parquet.unlink()
        backup = self.settings.backup_path(task_id)
        backup.mkdir()
        (backup / "old.txt").write_text("old")

        with self.assertRaisesRegex(RuntimeError, "has no Parquet files"):
            self.run_refresh(aws)

        self.assertTrue(backup.is_dir())
        self.assertEqual((backup / "old.txt").read_text(), "old")

    def test_sync_failure_preserves_existing_directory(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings, sync_error=RuntimeError("simulated sync failure"))

        with self.assertRaisesRegex(RuntimeError, "simulated sync failure"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "downloading")

    def test_incomplete_export_preserves_existing_directory(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings, omit_parquet=True)

        with self.assertRaisesRegex(RuntimeError, "no Parquet files"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

    def test_export_objects_without_checksums_are_rejected_before_download(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.omit_checksum = True

        with self.assertRaisesRegex(RuntimeError, "does not expose an S3 checksum"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

    def test_completed_export_with_warning_is_rejected_before_download(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.warning_message = '{"skippedTables":["postgres.public.problem"]}'
        first_task = "transformity-production-no-audit-scraper-20260724-180000"

        with self.assertRaisesRegex(RuntimeError, "completed with a warning"):
            self.run_refresh(aws)

        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "rejected")
        self.assertEqual(state["task_id"], first_task)
        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

        aws.warning_message = None
        self.now += timedelta(seconds=1)
        result = self.run_refresh(aws, force=True)

        second_task = "transformity-production-no-audit-scraper-20260724-180001"
        self.assertTrue(result.changed)
        self.assertEqual(result.task_id, second_task)
        self.assertEqual(aws.started, [first_task, second_task])

    def test_incomplete_table_metadata_preserves_existing_directory(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.table_status = "FAILED"

        with self.assertRaisesRegex(
            RuntimeError, "table metadata is incomplete.*postgres.public.example"
        ):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        state = json.loads(self.state_file.read_text())
        self.assertEqual(state["phase"], "rejected")
        rejected_staging = self.settings.staging_path(state["task_id"])
        self.assertTrue(rejected_staging.is_dir())

        aws.table_status = "COMPLETE"
        self.now += timedelta(seconds=1)
        result = self.run_refresh(aws)

        self.assertTrue(result.changed)
        self.assertFalse(rejected_staging.exists())

    def test_data_object_outside_requested_scopes_is_rejected(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.extra_scope_object = True

        with self.assertRaisesRegex(RuntimeError, "outside requested export scopes"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

    def test_nested_metadata_key_cannot_bypass_scope_validation(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.nested_metadata_key = True

        with self.assertRaisesRegex(RuntimeError, "unexpected table metadata key"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

    def test_malformed_data_key_is_rejected_before_download(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.malformed_data_key = True

        with self.assertRaisesRegex(RuntimeError, "unexpected export data key"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")
        self.assertEqual(aws.synced, [])

    def test_table_metadata_outside_requested_scopes_is_rejected(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings)
        aws.extra_table_target = True

        with self.assertRaisesRegex(RuntimeError, "table target outside export scopes"):
            self.run_refresh(aws)

        self.assertEqual((self.target / "current.txt").read_text(), "keep")

    def test_wrong_aws_account_is_rejected_before_mutation(self):
        self.target.mkdir()
        (self.target / "current.txt").write_text("keep")
        aws = FakeAWS(self.settings, account_id="111111111111")

        with self.assertRaisesRegex(RuntimeError, "expected AWS account"):
            self.run_refresh(aws)

        self.assertEqual(aws.started, [])
        self.assertEqual((self.target / "current.txt").read_text(), "keep")

    def test_invalid_saved_task_identifier_is_rejected_before_path_use(self):
        exporter.save_state(
            self.state_file,
            {
                "version": 1,
                "phase": "installed",
                "task_id": "../../escape",
                "installed_at": (self.now - timedelta(days=1)).isoformat(),
            },
        )
        aws = FakeAWS(self.settings)

        with self.assertRaisesRegex(RuntimeError, "unsafe RDS export task identifier"):
            self.run_refresh(aws)

        self.assertEqual(aws.started, [])
        self.assertEqual(aws.synced, [])

    def test_successful_main_run_is_silent(self):
        aws = FakeAWS(self.settings)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch.object(exporter, "Settings", return_value=self.settings),
            mock.patch.object(exporter, "AWSClient", return_value=aws),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = exporter.main(["--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_failed_main_run_is_nonzero_and_writes_stderr(self):
        aws = FakeAWS(self.settings, account_id="111111111111")
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch.object(exporter, "Settings", return_value=self.settings),
            mock.patch.object(exporter, "AWSClient", return_value=aws),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = exporter.main(["--force"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Weekly production DB export failed", stderr.getvalue())

    def test_lock_contention_is_a_silent_noop(self):
        self.settings.lock_file.parent.mkdir(parents=True)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with self.settings.lock_file.open("a+") as held_lock:
            exporter.fcntl.flock(
                held_lock.fileno(), exporter.fcntl.LOCK_EX | exporter.fcntl.LOCK_NB
            )
            with (
                mock.patch.object(exporter, "Settings", return_value=self.settings),
                mock.patch.object(exporter, "AWSClient") as aws_client,
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = exporter.main(["--force"])

        self.assertEqual(exit_code, 0)
        aws_client.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_s3_download_enables_checksum_validation(self):
        client = exporter.AWSClient(self.settings, binary="/usr/bin/aws")
        completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")

        with mock.patch.object(
            exporter.subprocess, "run", return_value=completed
        ) as run:
            client.sync_export("export-task", self.target)

        command = run.call_args.args[0]
        checksum_option = command.index("--checksum-mode")
        self.assertEqual(command[checksum_option + 1], "ENABLED")

    def test_start_export_uses_live_cluster_arn_and_exact_requested_scopes(self):
        client = exporter.AWSClient(self.settings, binary="/usr/bin/aws")
        completed = subprocess.CompletedProcess([], 0, stdout="{}", stderr="")
        task_id = "transformity-production-no-audit-scraper-20260724-180000"

        with mock.patch.object(
            exporter.subprocess, "run", return_value=completed
        ) as run:
            client.start_export(task_id)

        command = run.call_args.args[0]
        source_option = command.index("--source-arn")
        self.assertEqual(
            command[source_option + 1],
            "arn:aws:rds:us-east-1:928004597368:cluster:transformity-production",
        )
        export_only_option = command.index("--export-only")
        self.assertEqual(
            command[export_only_option + 1 : export_only_option + 3],
            ["postgres.reference", "postgres.public"],
        )


if __name__ == "__main__":
    unittest.main()
