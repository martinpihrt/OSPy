import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import threading
import unittest
from unittest import mock
import zipfile

from tests.test_support import TEST_DATA_DIR

from ospy import i18n  # Install the same gettext function used by a running OSPy.
import plugins
from ospy import options as options_module


ROOT = Path(__file__).resolve().parents[1]
CORE_PLUGIN_ROOT = ROOT / "plugins"


def _configured_official_plugin_roots():
    value = os.environ.get("OSPY_PLUGIN_ROOTS", "")
    if not value:
        return []
    return [
        Path(item).expanduser().resolve()
        for item in value.split(os.pathsep)
        if item.strip()
    ]


def _plugin_directories(plugin_root):
    if not plugin_root.is_dir():
        return []
    return sorted(
        directory
        for directory in plugin_root.iterdir()
        if directory.is_dir() and (directory / "__init__.py").is_file()
    )


def _plugin_archive(plugin_definitions):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        for plugin, manifest in plugin_definitions.items():
            base = "repository/plugins/{}".format(plugin)
            zip_file.writestr(
                base + "/__init__.py",
                "NAME = {!r}\nMENU = {!r}\n"
                "def start():\n    pass\n"
                "def stop():\n    pass\n".format(plugin, plugin),
            )
            zip_file.writestr(base + "/README.md", "# {}".format(plugin))
            if manifest is not None:
                if isinstance(manifest, bytes):
                    contents = manifest
                else:
                    contents = json.dumps(manifest).encode("utf-8")
                zip_file.writestr(base + "/plugin.json", contents)
    archive.seek(0)
    return archive


def _manifest(plugin, **changes):
    result = {
        "schema_version": 1,
        "id": plugin,
        "name": plugin,
        "version": "1.0.0",
        "ospy": {"min": "3.0.0"},
        "python": {"min": "3.8"},
        "requirements": [],
        "permissions": [],
    }
    result.update(changes)
    return result


class PluginManifestParserTests(unittest.TestCase):
    def test_tests_use_isolated_data_without_background_plugin_checker(self):
        self.assertTrue(
            os.path.realpath(options_module.OPTIONS_FILE).startswith(
                os.path.realpath(TEST_DATA_DIR) + os.sep
            )
        )
        self.assertFalse(plugins.checker.is_alive())

    def test_valid_manifest_is_normalized(self):
        manifest = {
            "schema_version": 1,
            "id": "example_plugin",
            "name": "Example Plugin",
            "version": "1.0.0",
            "homepage": "https://example.com/plugin",
            "ospy": {"min": "3.0.0"},
            "python": {"min": "3.8"},
            "requirements": [],
            "hardware": {},
            "permissions": ["network"],
            "conflicts": [],
        }
        normalized = plugins._manifest_from_bytes(
            json.dumps(manifest).encode("utf-8"), "example_plugin"
        )
        self.assertEqual(normalized["id"], "example_plugin")
        self.assertEqual(normalized["schema_version"], 1)
        self.assertEqual(normalized["name"], "Example Plugin")

    def test_invalid_manifests_are_rejected(self):
        invalid = (
            ({"schema_version": 0, "id": "example_plugin"}, "example_plugin"),
            ({"schema_version": True, "id": "example_plugin"}, "example_plugin"),
            ({"schema_version": 1, "id": "different_plugin"}, "example_plugin"),
            ({"schema_version": 1, "id": "Invalid ID"}, None),
            (
                {
                    "schema_version": 1,
                    "id": "example_plugin",
                    "homepage": "ftp://example.com",
                },
                "example_plugin",
            ),
            (
                {
                    "schema_version": 1,
                    "id": "example_plugin",
                    "requirements": "requests",
                },
                "example_plugin",
            ),
        )
        for manifest, module in invalid:
            with self.subTest(manifest=manifest, module=module):
                self.assertEqual(
                    plugins._manifest_from_bytes(
                        json.dumps(manifest).encode("utf-8"), module
                    ),
                    {},
                )

    def test_selectable_i2c_manifest_is_validated_and_normalized(self):
        manifest = _manifest(
            "selector_plugin",
            hardware={
                "requires": ["i2c"],
                "i2c": [{
                    "alternatives": ["0X50", "0x51"],
                    "option": "address",
                    "option_values": {"0x50": False, "0x51": True},
                    "default": "0X50",
                }],
            },
        )
        normalized = plugins._normalize_plugin_manifest(
            manifest, "selector_plugin"
        )

        declaration = normalized["hardware"]["i2c"][0]
        self.assertEqual(declaration["alternatives"], ["0x50", "0x51"])
        self.assertEqual(declaration["default"], "0x50")

        manifest["hardware"]["i2c"][0]["option_values"].pop("0x51")
        self.assertEqual(
            plugins._normalize_plugin_manifest(manifest, "selector_plugin"),
            {},
        )

    def test_selectable_i2c_addresses_share_distinct_alternatives(self):
        selectable = _manifest(
            "selector_plugin",
            hardware={
                "i2c": [{
                    "alternatives": ["0x50", "0x51"],
                    "option": "address",
                    "option_values": {"0x50": False, "0x51": True},
                    "default": "0x50",
                }],
            },
        )
        other_selectable = _manifest(
            "other_selector",
            hardware={
                "i2c": [{
                    "alternatives": ["0x50", "0x51"],
                    "option": "address",
                    "option_values": {"0x50": False, "0x51": True},
                    "default": "0x50",
                }],
            },
        )
        fixed = _manifest("fixed_plugin", hardware={"i2c": ["0x50"]})

        with mock.patch.object(
            plugins,
            "plugin_manifest",
            side_effect=lambda module: {
                "other_selector": other_selectable,
                "fixed_plugin": fixed,
            }.get(module, {}),
        ):
            compatible = plugins.plugin_manifest_compatibility(
                "selector_plugin",
                selectable,
                enabled_modules=["other_selector"],
            )
            exhausted = plugins.plugin_manifest_compatibility(
                "selector_plugin",
                selectable,
                enabled_modules=["other_selector", "fixed_plugin"],
            )

        self.assertTrue(compatible["compatible"])
        self.assertFalse(exhausted["compatible"])
        self.assertTrue(any(
            "selectable" in error.lower() for error in exhausted["errors"]
        ))

    def test_selected_i2c_address_uses_option_mapping(self):
        manifest = _manifest(
            "selector_plugin",
            hardware={
                "i2c": [{
                    "alternatives": ["0x50", "0x51"],
                    "option": "address",
                    "option_values": {"0x50": False, "0x51": True},
                    "default": "0x50",
                }],
            },
        )

        self.assertEqual(
            plugins._selected_i2c_resources(
                "selector_plugin", manifest, {"address": True}
            ),
            {"0x51"},
        )
        self.assertEqual(
            plugins._selected_i2c_resources("selector_plugin", manifest, {}),
            {"0x50"},
        )

    def test_select_plugin_i2c_address_uses_free_alternative(self):
        def selectable_manifest(plugin):
            return _manifest(
                plugin,
                hardware={
                    "i2c": [{
                        "alternatives": ["0x50", "0x51"],
                        "option": "address",
                        "option_values": {"0x50": False, "0x51": True},
                        "default": "0x50",
                    }],
                },
            )

        storage_key = "plugin_other_selector"
        had_original = storage_key in options_module.options
        original = options_module.options[storage_key] if had_original else None
        options_module.options[storage_key] = {"address": True}
        try:
            with mock.patch.object(
                plugins,
                "plugin_manifest",
                side_effect=lambda module: selectable_manifest(module),
            ):
                self.assertEqual(
                    plugins.plugin_i2c_address_conflict(
                        "selector_plugin", "0x51", ["other_selector"]
                    ),
                    "other_selector",
                )
                self.assertEqual(
                    plugins.select_plugin_i2c_address(
                        "selector_plugin", "0x51", ["other_selector"]
                    ),
                    "0x50",
                )
        finally:
            if not had_original:
                del options_module.options[storage_key]
            else:
                options_module.options[storage_key] = original

    def test_plugin_page_metadata_uses_manifest_version(self):
        manifest = _manifest(
            "example_plugin",
            name="Example Plugin",
            version="1.2.3",
        )
        with mock.patch.object(
            plugins, "running", return_value=["example_plugin"]
        ), mock.patch.object(
            plugins, "plugin_manifest", return_value=manifest
        ):
            metadata = plugins.plugin_page_metadata(
                "/example_plugin/settings?section=main"
            )

        self.assertEqual(metadata["name"], "Example Plugin")
        self.assertEqual(metadata["version"], "1.2.3")
        self.assertEqual(plugins.plugin_page_metadata("/plugins_manage"), {})

    def test_plugin_repository_follows_validated_update_channel(self):
        with mock.patch.object(
            options_module, "options", mock.Mock(plugin_update_channel="beta")
        ):
            self.assertEqual(plugins.plugin_update_channel(), "beta")
            self.assertEqual(
                plugins.plugin_repositories(),
                ["https://github.com/martinpihrt/OSPy-plugins/archive/beta.zip"],
            )

        with mock.patch.object(
            options_module, "options", mock.Mock(plugin_update_channel="unknown")
        ):
            self.assertEqual(plugins.plugin_update_channel(), "master")
            self.assertEqual(
                plugins.plugin_repositories(),
                ["https://github.com/martinpihrt/OSPy-plugins/archive/master.zip"],
            )

    def test_custom_plugin_repository_override_is_preserved(self):
        with mock.patch.object(plugins, "REPOS", ["test-repository"]):
            self.assertEqual(plugins.plugin_repositories(), ["test-repository"])

    def test_bulk_permission_approval_uses_one_persistent_write(self):
        original_initialized = (
            options_module.options.plugin_permission_approval_initialized
        )
        original_approvals = options_module.options.plugin_permission_approvals
        options_module.options.plugin_permission_approval_initialized = True
        options_module.options.plugin_permission_approvals = {}
        manifests = {
            "first_plugin": _manifest(
                "first_plugin", permissions=["network"]
            ),
            "second_plugin": _manifest(
                "second_plugin", permissions=["files", "gpio"]
            ),
        }
        try:
            with mock.patch.object(
                plugins, "available", return_value=list(manifests)
            ), mock.patch.object(
                plugins, "plugin_manifest",
                side_effect=lambda module: manifests[module],
            ), mock.patch.object(
                options_module._Options, "save_now", return_value=True
            ) as save_now:
                approved = plugins.approve_all_plugin_permissions(
                    approved_by="admin"
                )
        finally:
            stored = dict(options_module.options.plugin_permission_approvals)
            options_module.options.plugin_permission_approval_initialized = (
                original_initialized
            )
            options_module.options.plugin_permission_approvals = (
                original_approvals
            )

        self.assertEqual(set(approved), set(manifests))
        self.assertEqual(stored["first_plugin"]["permissions"], ["network"])
        self.assertEqual(
            stored["second_plugin"]["permissions"], ["files", "gpio"]
        )
        save_now.assert_called_once_with()


class PluginArchiveInstallationTests(unittest.TestCase):
    def test_selectable_i2c_plugins_install_together_from_zip(self):
        def manifest(plugin):
            return _manifest(
                plugin,
                hardware={
                    "i2c": [{
                        "alternatives": ["0x50", "0x51"],
                        "option": "address",
                        "option_values": {"0x50": False, "0x51": True},
                        "default": "0x50",
                    }],
                },
            )

        archive = _plugin_archive({
            "wind_monitor": manifest("wind_monitor"),
            "water_meter": manifest("water_meter"),
        })
        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(archive)

        self.assertEqual(
            set(result["installed"]), {"wind_monitor", "water_meter"}
        )
        self.assertEqual(install_plugin.call_count, 2)

    def test_unsafe_parent_path_is_rejected_before_any_write(self):
        archive = _plugin_archive({"safe_plugin": _manifest("safe_plugin")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(
                "repository/plugins/safe_plugin/../outside.py", "unsafe"
            )
        archive.seek(0)

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

        install_docs.assert_not_called()
        install_plugin.assert_not_called()

    def test_duplicate_archive_path_is_rejected(self):
        archive = _plugin_archive({"duplicate_plugin": _manifest("duplicate_plugin")})
        with self.assertWarns(UserWarning):
            with zipfile.ZipFile(archive, "a") as zip_file:
                zip_file.writestr(
                    "repository/plugins/duplicate_plugin/README.md", "duplicate"
                )
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_duplicate_plugin_identifier_is_rejected(self):
        archive = io.BytesIO()
        manifest = json.dumps(_manifest("duplicate_plugin"))
        with zipfile.ZipFile(archive, "w") as zip_file:
            for root in ("repository-one", "repository-two"):
                base = root + "/plugins/duplicate_plugin"
                zip_file.writestr(base + "/__init__.py", "NAME = 'Duplicate'\n")
                zip_file.writestr(base + "/plugin.json", manifest)
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_symbolic_link_entry_is_rejected(self):
        archive = _plugin_archive({"link_plugin": _manifest("link_plugin")})
        link_info = zipfile.ZipInfo(
            "repository/plugins/link_plugin/linked-file"
        )
        link_info.create_system = 3
        link_info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(link_info, "../../outside")
        archive.seek(0)

        with self.assertRaises(ValueError):
            plugins.checker.install_custom_plugin(archive)

    def test_archive_size_limit_is_enforced_before_installation(self):
        archive = _plugin_archive({"large_plugin": _manifest("large_plugin")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr(
                "repository/plugins/large_plugin/large.bin", b"x" * 128
            )
        archive.seek(0)

        with mock.patch.object(
            plugins, "PLUGIN_ZIP_MAX_TOTAL_BYTES", 64
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

        install_plugin.assert_not_called()

    def test_archive_file_count_limit_is_enforced(self):
        archive = _plugin_archive({"many_files": _manifest("many_files")})
        with zipfile.ZipFile(archive, "a") as zip_file:
            zip_file.writestr("repository/plugins/many_files/extra.txt", "extra")
        archive.seek(0)

        with mock.patch.object(plugins, "PLUGIN_ZIP_MAX_FILES", 3):
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

    def test_suspicious_compression_ratio_is_rejected(self):
        archive = _plugin_archive({"compressed_plugin": _manifest("compressed_plugin")})
        with zipfile.ZipFile(archive, "a", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                "repository/plugins/compressed_plugin/repeated.bin",
                b"0" * 4096,
            )
        archive.seek(0)

        with mock.patch.object(plugins, "PLUGIN_ZIP_MAX_RATIO", 2):
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(archive)

    def test_atomic_update_preserves_plugin_data(self):
        archive = _plugin_archive({"atomic_plugin": _manifest("atomic_plugin")})
        with tempfile.TemporaryDirectory(prefix="ospy-plugin-data-") as root:
            target_dir = os.path.join(root, "atomic_plugin")
            data_dir = os.path.join(target_dir, "data")
            os.makedirs(data_dir)
            with open(
                os.path.join(target_dir, "__init__.py"), "w", encoding="utf-8"
            ) as file_handle:
                file_handle.write("NAME = 'Old version'\n")
            with open(
                os.path.join(data_dir, "settings.json"), "w", encoding="utf-8"
            ) as file_handle:
                file_handle.write('{"preserved": true}')

            def test_plugin_dir(module=None):
                return os.path.join(root, module) if module else root

            with mock.patch.object(
                plugins, "plugin_dir", side_effect=test_plugin_dir
            ):
                plugins.checker._install_plugin(
                    archive,
                    "atomic_plugin",
                    "repository/plugins/atomic_plugin",
                )

            with open(
                os.path.join(target_dir, "data", "settings.json"),
                encoding="utf-8",
            ) as file_handle:
                self.assertEqual(file_handle.read(), '{"preserved": true}')
            with open(
                os.path.join(target_dir, "plugin.json"), encoding="utf-8"
            ) as file_handle:
                self.assertEqual(json.load(file_handle)["id"], "atomic_plugin")

    def test_failed_directory_swap_restores_previous_plugin(self):
        archive = _plugin_archive({"atomic_plugin": _manifest("atomic_plugin")})
        with tempfile.TemporaryDirectory(prefix="ospy-plugin-atomic-") as root:
            target_dir = os.path.join(root, "atomic_plugin")
            os.makedirs(target_dir)
            old_init = os.path.join(target_dir, "__init__.py")
            with open(old_init, "w", encoding="utf-8") as file_handle:
                file_handle.write("NAME = 'Old version'\n")

            real_replace = os.replace
            replace_calls = []

            def failing_replace(source, target):
                replace_calls.append((source, target))
                if len(replace_calls) == 2:
                    raise OSError("simulated swap failure")
                return real_replace(source, target)

            def test_plugin_dir(module=None):
                return os.path.join(root, module) if module else root

            with mock.patch.object(
                plugins, "plugin_dir", side_effect=test_plugin_dir
            ), mock.patch("os.replace", side_effect=failing_replace):
                with self.assertRaisesRegex(OSError, "simulated swap failure"):
                    plugins.checker._install_plugin(
                        archive,
                        "atomic_plugin",
                        "repository/plugins/atomic_plugin",
                    )

            with open(old_init, encoding="utf-8") as file_handle:
                self.assertEqual(file_handle.read(), "NAME = 'Old version'\n")
            self.assertFalse(
                any(name.startswith(".ospy-plugin-install-") for name in os.listdir(root))
            )

    def test_archive_reports_missing_and_invalid_manifests_as_incompatible(self):
        archive = _plugin_archive({
            "missing_manifest": None,
            "invalid_manifest": b"{not json",
        })
        contents = plugins.checker.zip_contents(archive, load_read_me=False)

        self.assertFalse(contents["missing_manifest"]["compatibility"]["compatible"])
        self.assertFalse(contents["missing_manifest"]["manifest_present"])
        self.assertTrue(
            contents["missing_manifest"]["compatibility"]["errors"]
        )
        self.assertFalse(contents["invalid_manifest"]["compatibility"]["compatible"])
        self.assertTrue(contents["invalid_manifest"]["manifest_present"])
        self.assertFalse(contents["invalid_manifest"]["manifest_valid"])
        self.assertTrue(
            contents["invalid_manifest"]["compatibility"]["errors"]
        )

    def test_incompatible_single_plugin_is_blocked_before_any_write(self):
        archive = _plugin_archive({
            "future_plugin": _manifest(
                "future_plugin", ospy={"min": "9999.0"}
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(
                    archive, "future_plugin"
                )

        install_docs.assert_not_called()
        install_plugin.assert_not_called()

    def test_incompatible_update_is_installed_but_not_activated(self):
        archive = _plugin_archive({
            "future_plugin": _manifest(
                "future_plugin", ospy={"min": "9999.0"}
            ),
        })

        with mock.patch.object(
            plugins, "available", return_value=["future_plugin"]
        ), mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(
                archive, "future_plugin"
            )

        self.assertEqual(result["installed"], ["future_plugin"])
        self.assertIn("future_plugin", result["warnings"])
        self.assertNotIn("future_plugin", result["blocked"])
        install_plugin.assert_called_once()
        self.assertFalse(install_plugin.call_args.kwargs["activate"])

    def test_bulk_install_skips_incompatible_and_installs_compatible_plugins(self):
        archive = _plugin_archive({
            "compatible_plugin": _manifest("compatible_plugin"),
            "future_plugin": _manifest(
                "future_plugin", ospy={"min": "9999.0"}
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(archive)

        self.assertEqual(result["installed"], ["compatible_plugin"])
        self.assertIn("future_plugin", result["blocked"])
        install_docs.assert_called_once()
        self.assertEqual(install_plugin.call_count, 1)
        self.assertEqual(install_plugin.call_args.args[1], "compatible_plugin")

    def test_selected_plugin_list_updates_only_requested_plugins(self):
        archive = _plugin_archive({
            "first_plugin": _manifest("first_plugin"),
            "second_plugin": _manifest("second_plugin"),
            "unselected_plugin": _manifest("unselected_plugin"),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(
                archive, ["first_plugin", "second_plugin"]
            )

        self.assertEqual(
            set(result["installed"]), {"first_plugin", "second_plugin"}
        )
        self.assertEqual(
            {call.args[1] for call in install_plugin.call_args_list},
            {"first_plugin", "second_plugin"},
        )

    def test_update_all_selects_only_changed_installed_plugins(self):
        checker = object.__new__(plugins._PluginChecker)
        checker._lock = threading.RLock()
        repository_info = {
            "changed_plugin": {
                "hash": "new-hash",
                "repo": "test-repository",
            },
            "current_plugin": {
                "hash": "same-hash",
                "repo": "test-repository",
            },
            "not_installed": {
                "hash": "new-hash",
                "repo": "test-repository",
            },
        }
        original_status = options_module.options.plugin_status
        options_module.options.plugin_status = {
            "changed_plugin": {"hash": "old-hash"},
            "current_plugin": {"hash": "same-hash"},
        }
        try:
            with mock.patch.object(
                checker, "cached_available_versions",
                return_value=repository_info,
            ), mock.patch.object(
                plugins, "available",
                return_value=["changed_plugin", "current_plugin"],
            ), mock.patch.object(
                checker, "_get_zip", return_value=io.BytesIO()
            ), mock.patch.object(
                checker, "install_custom_plugin",
                return_value={
                    "installed": ["changed_plugin"],
                    "blocked": {},
                    "warnings": {},
                    "permissions_approved": [],
                },
            ) as install_plugins:
                result = checker.install_available_updates(
                    approve_permissions=True,
                    approved_by="admin",
                )
        finally:
            options_module.options.plugin_status = original_status

        self.assertEqual(result["installed"], ["changed_plugin"])
        install_plugins.assert_called_once_with(
            mock.ANY,
            plugin_filter=["changed_plugin"],
            approve_permissions=True,
            approved_by="admin",
        )

    def test_bulk_install_orders_required_dependency_before_consumer(self):
        archive = _plugin_archive({
            "dependent_plugin": _manifest(
                "dependent_plugin",
                dependencies=[{"id": "provider_plugin", "required": True}],
            ),
            "provider_plugin": _manifest("provider_plugin"),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(archive)

        self.assertEqual(
            result["installed"], ["provider_plugin", "dependent_plugin"]
        )
        self.assertEqual(
            [call.args[1] for call in install_plugin.call_args_list],
            ["provider_plugin", "dependent_plugin"],
        )

    def test_single_consumer_install_requires_installed_provider(self):
        archive = _plugin_archive({
            "dependent_plugin": _manifest(
                "dependent_plugin",
                dependencies=[{"id": "provider_plugin", "required": True}],
            ),
            "provider_plugin": _manifest("provider_plugin"),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ) as install_docs, mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            with self.assertRaises(ValueError):
                plugins.checker.install_custom_plugin(
                    archive, "dependent_plugin"
                )

        install_docs.assert_not_called()
        install_plugin.assert_not_called()

    def test_compatibility_warning_does_not_block_installation(self):
        archive = _plugin_archive({
            "warning_plugin": _manifest(
                "warning_plugin", permissions=["unknown-permission"]
            ),
        })

        with mock.patch.object(
            plugins.checker, "_install_repo_docs"
        ), mock.patch.object(
            plugins.checker, "_install_plugin"
        ) as install_plugin:
            result = plugins.checker.install_custom_plugin(
                archive, "warning_plugin"
            )

        self.assertEqual(result["installed"], ["warning_plugin"])
        self.assertIn("warning_plugin", result["warnings"])
        install_plugin.assert_called_once()

    def test_automatic_update_skips_incompatible_available_version(self):
        checker = object.__new__(plugins._PluginChecker)
        checker._lock = threading.RLock()
        checker._repo_data = {}
        checker._repo_contents = {}
        checker._changes_cache = {}
        update = {
            "repo": "test-repository",
            "hash": "new-hash",
            "compatibility": {
                "compatible": False,
                "errors": ["Unsupported OSPy version."],
            },
        }

        with mock.patch.object(plugins, "REPOS", ["test-repository"]), \
                mock.patch.object(checker, "_download_zip", return_value=io.BytesIO()), \
                mock.patch.object(checker, "zip_contents", return_value={}), \
                mock.patch.object(plugins, "available", return_value=["future_plugin"]), \
                mock.patch.object(checker, "available_version", return_value=update), \
                mock.patch.object(checker, "sync_installed_status", return_value=False), \
                mock.patch.object(checker, "install_repo_plugin") as install_plugin:
            with self.assertLogs(level="WARNING") as captured:
                checker.refresh(install_updates=True)

        install_plugin.assert_not_called()
        self.assertTrue(
            any("future_plugin" in message for message in captured.output)
        )


class PluginDiagnosticsCollectionTests(unittest.TestCase):
    def setUp(self):
        setattr(plugins, "__plugin_diagnostics_cache", {"time": 0, "data": None})

    def test_simultaneous_diagnostics_requests_reuse_short_cache(self):
        result = [{"module": "cached_plugin"}]
        with mock.patch.object(
            plugins, "_plugin_diagnostics_uncached", return_value=result
        ) as collect:
            first = plugins.plugin_diagnostics()
            second = plugins.plugin_diagnostics()

        self.assertIs(first, result)
        self.assertIs(second, result)
        collect.assert_called_once_with()

    def test_forced_diagnostics_refresh_bypasses_cache(self):
        with mock.patch.object(
            plugins,
            "_plugin_diagnostics_uncached",
            side_effect=([{"sample": 1}], [{"sample": 2}]),
        ) as collect:
            first = plugins.plugin_diagnostics()
            second = plugins.plugin_diagnostics(force=True)

        self.assertEqual(first, [{"sample": 1}])
        self.assertEqual(second, [{"sample": 2}])
        self.assertEqual(collect.call_count, 2)


class PluginManifestRepositoryTests(unittest.TestCase):
    def _validate_manifest(self, plugin_dir):
        manifest_path = plugin_dir / plugins.PLUGIN_MANIFEST_FILE
        self.assertLessEqual(
            manifest_path.stat().st_size,
            plugins.PLUGIN_MANIFEST_MAX_BYTES,
            "{} exceeds the manifest size limit.".format(manifest_path),
        )
        normalized = plugins._manifest_from_bytes(
            manifest_path.read_bytes(), plugin_dir.name
        )
        self.assertTrue(normalized, "{} is invalid.".format(manifest_path))
        self.assertEqual(normalized.get("id"), plugin_dir.name)
        self.assertEqual(
            normalized.get("schema_version"), plugins.PLUGIN_MANIFEST_SCHEMA_VERSION
        )
        self.assertTrue(normalized.get("name"), "{} has no name.".format(manifest_path))
        self.assertTrue(
            normalized.get("version"), "{} has no version.".format(manifest_path)
        )

    def test_installed_plugin_manifests_are_valid(self):
        for plugin_dir in _plugin_directories(CORE_PLUGIN_ROOT):
            manifest_path = plugin_dir / plugins.PLUGIN_MANIFEST_FILE
            if manifest_path.is_file():
                with self.subTest(plugin=plugin_dir.name):
                    self._validate_manifest(plugin_dir)

    def test_official_plugin_roots_have_valid_manifests_for_every_plugin(self):
        for plugin_root in _configured_official_plugin_roots():
            with self.subTest(plugin_root=str(plugin_root)):
                self.assertTrue(
                    plugin_root.is_dir(),
                    "Configured plug-in root does not exist: {}".format(plugin_root),
                )
                plugin_dirs = _plugin_directories(plugin_root)
                self.assertTrue(
                    plugin_dirs,
                    "No plug-ins were found in {}".format(plugin_root),
                )
                missing = [
                    plugin_dir.name
                    for plugin_dir in plugin_dirs
                    if not (plugin_dir / plugins.PLUGIN_MANIFEST_FILE).is_file()
                ]
                self.assertFalse(
                    missing,
                    "Plug-ins without plugin.json in {}:\n{}".format(
                        plugin_root, "\n".join(missing)
                    ),
                )
                for plugin_dir in plugin_dirs:
                    with self.subTest(
                        plugin_root=str(plugin_root), plugin=plugin_dir.name
                    ):
                        self._validate_manifest(plugin_dir)

    def test_official_mobile_adapters_declare_contract_and_functions(self):
        expected = {
            "air_temp_humi",
            "chmi",
            "current_loop_tanks_monitor",
            "real_time",
            "shelly_cloud_integrator",
            "sunrise_and_sunset",
            "system_info",
            "tank_monitor",
            "ups_adj",
            "water_consumption_counter",
            "weather_based_water_level",
            "wind_monitor",
        }
        roots = _configured_official_plugin_roots()
        if not roots:
            self.skipTest("No official plug-in root is configured.")
        plugin_dirs = {
            plugin_dir.name: plugin_dir
            for root in roots
            for plugin_dir in _plugin_directories(root)
        }
        self.assertFalse(expected - set(plugin_dirs))

        for module in sorted(expected):
            with self.subTest(plugin=module):
                plugin_dir = plugin_dirs[module]
                manifest = json.loads(
                    (plugin_dir / plugins.PLUGIN_MANIFEST_FILE).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(manifest.get("mobile", {}).get("api_version"), 1)
                source = (plugin_dir / "__init__.py").read_text(encoding="utf-8")
                self.assertIn("def mobile_status(", source)
                self.assertIn("def mobile_cards(", source)


if __name__ == "__main__":
    unittest.main()
