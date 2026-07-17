import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation

from ospy import backup


class SystemBackupTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ospy-backup-test-")
        data = Path(self.root, "ospy", "data", "default")
        images = Path(self.root, "ospy", "images", "stations")
        data.mkdir(parents=True)
        images.mkdir(parents=True)
        (data / "options.db.dat").write_bytes(b"settings")
        (Path(self.root, "ospy", "data") / "events.log").write_text(
            "event", encoding="utf-8"
        )
        (images / "1.png").write_bytes(b"image")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_created_backup_has_manifest_checksums_and_expected_scope(self):
        archive = backup.create_system_backup(root=self.root, reason="test")
        manifest = backup.inspect_backup(archive)
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["reason"], "test")
        self.assertEqual(
            {entry["path"] for entry in manifest["files"]},
            {
                "ospy/data/default/options.db.dat",
                "ospy/data/events.log",
                "ospy/images/stations/1.png",
            },
        )

    def test_tampered_payload_is_rejected(self):
        original = backup.create_system_backup(root=self.root)
        tampered = os.path.join(self.root, "tampered.zip")
        with zipfile.ZipFile(original, "r") as source, zipfile.ZipFile(tampered, "w") as target:
            for info in source.infolist():
                contents = source.read(info)
                if info.filename == "ospy/data/events.log":
                    contents = b"changed"
                target.writestr(info.filename, contents)
        with self.assertRaises(backup.BackupError):
            backup.inspect_backup(tampered)

    def test_undeclared_and_out_of_scope_files_are_rejected(self):
        original = backup.create_system_backup(root=self.root)
        invalid = os.path.join(self.root, "invalid.zip")
        with zipfile.ZipFile(original, "r") as source, zipfile.ZipFile(invalid, "w") as target:
            for info in source.infolist():
                target.writestr(info.filename, source.read(info))
            target.writestr("ospy/server.py", b"not allowed")
        with self.assertRaises(backup.BackupError):
            backup.inspect_backup(invalid)

    def test_traversal_and_duplicate_paths_are_rejected(self):
        for members in (
            [("../outside", b"x")],
            [("C:/outside", b"x")],
            [("default//options.db.dat", b"x")],
            [("default/a", b"x"), ("DEFAULT/A", b"y")],
        ):
            path = os.path.join(self.root, "unsafe.zip")
            with zipfile.ZipFile(path, "w") as archive:
                for name, contents in members:
                    archive.writestr(name, contents)
            with self.assertRaises(backup.BackupError):
                backup.inspect_backup(path)

    def test_symbolic_link_and_expanded_size_limit_are_rejected(self):
        symbolic = os.path.join(self.root, "symbolic.zip")
        info = zipfile.ZipInfo("default/link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(symbolic, "w") as archive:
            archive.writestr(info, "target")
        with self.assertRaises(backup.BackupError):
            backup.inspect_backup(symbolic)

        oversized = os.path.join(self.root, "oversized.zip")
        with zipfile.ZipFile(oversized, "w") as archive:
            archive.writestr("default/options.db.dat", b"12345")
        with mock.patch.object(backup, "MAX_EXPANDED_SIZE", 4):
            with self.assertRaises(backup.BackupError):
                backup.inspect_backup(oversized)

    def test_legacy_backup_is_staged_only_below_ospy_data(self):
        path = os.path.join(self.root, "legacy.zip")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("default/options.db.dat", b"legacy")
            archive.writestr("events.log", b"old event")
        staging, manifest = backup.stage_restore(path, root=self.root)
        self.assertTrue(manifest["legacy"])
        self.assertEqual(
            Path(staging, "ospy", "data", "default", "options.db.dat").read_bytes(),
            b"legacy",
        )

    def test_verified_restore_replaces_data_and_station_images(self):
        archive = backup.create_system_backup(root=self.root)
        Path(self.root, "ospy", "data", "default", "options.db.dat").write_bytes(b"new")
        Path(self.root, "ospy", "images", "stations", "1.png").write_bytes(b"new image")
        staging, unused_manifest = backup.stage_restore(archive, root=self.root)
        backup.apply_staged_restore(staging, root=self.root)
        self.assertEqual(
            Path(self.root, "ospy", "data", "default", "options.db.dat").read_bytes(),
            b"settings",
        )
        self.assertEqual(
            Path(self.root, "ospy", "images", "stations", "1.png").read_bytes(),
            b"image",
        )

    def test_stored_backup_paths_are_safe_and_retention_keeps_ten_newest(self):
        backup_dir = Path(self.root, "ospy", "backup")
        backup_dir.mkdir(parents=True)
        for index in range(12):
            path = backup_dir / "backup-{:02d}.zip".format(index)
            path.write_bytes(b"zip")
            os.utime(path, (index + 1, index + 1))
        backup._prune_system_backups(str(backup_dir), keep=10)
        names = [item["name"] for item in backup.list_system_backups(root=self.root)]
        self.assertEqual(len(names), 10)
        self.assertEqual(names[0], "backup-11.zip")
        self.assertNotIn("backup-00.zip", names)
        self.assertIsNone(backup.system_backup_path("../backup-11.zip", root=self.root))
        self.assertEqual(
            backup.system_backup_path("backup-11.zip", root=self.root),
            str(backup_dir / "backup-11.zip"),
        )

    def test_failed_swap_restores_original_data(self):
        archive = backup.create_system_backup(root=self.root)
        current = Path(self.root, "ospy", "data", "default", "options.db.dat")
        current.write_bytes(b"current")
        staging, unused_manifest = backup.stage_restore(archive, root=self.root)
        real_replace = os.replace

        def fail_staged_move(source, target):
            if str(source).startswith(staging) and str(target).endswith(os.path.join("ospy", "data")):
                raise OSError("simulated failure")
            return real_replace(source, target)

        with mock.patch("ospy.backup.os.replace", side_effect=fail_staged_move):
            with self.assertRaises(OSError):
                backup.apply_staged_restore(staging, root=self.root)
        self.assertEqual(current.read_bytes(), b"current")


if __name__ == "__main__":
    unittest.main()
