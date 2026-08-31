from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(
    script: str,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


class MetadataTests(unittest.TestCase):
    def test_versions_match(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        installer = (SCRIPTS / "install_style_layer.py").read_text(encoding="utf-8")
        self.assertEqual(version, "1.1.0")
        self.assertEqual(manifest["version"], version)
        self.assertEqual(package["version"], version)
        self.assertIn(f'SKILL_VERSION = "{version}"', installer)

    def test_token_artifacts_are_current(self) -> None:
        result = run_script("generate_token_assets.py", str(ROOT))
        self.assertIn("66 canonical variables", result.stdout)


class InspectorTests(unittest.TestCase):
    def test_detects_frontend_stack_and_motion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            (target / "package.json").write_text(
                json.dumps(
                    {
                        "name": "fixture",
                        "dependencies": {
                            "react": "^19.0.0",
                            "tailwindcss": "^4.0.0",
                            "framer-motion": "^12.0.0",
                        },
                        "scripts": {"test": "vitest", "build": "vite build"},
                    }
                ),
                encoding="utf-8",
            )
            (target / "App.tsx").write_text(
                "export function App(){ return <button>Apply</button> }\n",
                encoding="utf-8",
            )
            (target / "styles.css").write_text(
                "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
                encoding="utf-8",
            )
            result = run_script("inspect_frontend.py", str(target), "--format", "json")
            report = json.loads(result.stdout)
            self.assertIn("React", report["detected"]["frameworks"])
            self.assertIn("Tailwind CSS", report["detected"]["styling"])
            self.assertIn("Framer Motion", report["detected"]["motion_libraries"])
            self.assertEqual(report["package"]["package_manager"], "unknown")
            self.assertIn("build", report["package"]["available_checks"])

    def test_rejects_escaping_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = run_script(
                "inspect_frontend.py",
                raw,
                "--output",
                "../outside.json",
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("escapes the target directory", result.stderr)


class VerificationTests(unittest.TestCase):
    def test_markdown_escapes_recommendation_table_separator(self) -> None:
        module_path = SCRIPTS / "verify_amicro_style.py"
        spec = importlib.util.spec_from_file_location("amicro_verify_test", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(SCRIPTS))
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(spec.name, None)
            sys.path.pop(0)

        markdown = module.render_markdown(
            {
                "target": "fixture",
                "status": "warn",
                "static_only": True,
                "scan": {"files": 1},
                "checks": [
                    {
                        "name": "Fixture",
                        "status": "warn",
                        "evidence": "one | two",
                        "recommendation": "keep | escaped",
                    }
                ],
                "findings": [],
                "manual_checks_required": [],
                "honesty_boundary": "Static evidence only.",
            }
        )
        self.assertIn("one \\| two", markdown)
        self.assertIn("keep \\| escaped", markdown)

    def test_bundled_style_passes_strict_static_checks(self) -> None:
        result = run_script(
            "verify_amicro_style.py",
            str(ROOT),
            "--strict",
            "--format",
            "json",
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_counts"]["fail"], 0)
        self.assertTrue(report["signals"]["token_parity"])

    def test_unsafe_animation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            (target / "unsafe.css").write_text(
                """
                :root { color-scheme: light dark; }
                button { animation: bounce 2s infinite; }
                @keyframes bounce { from { transform: translateY(0); }
                  to { transform: translateY(1rem); } }
                """,
                encoding="utf-8",
            )
            (target / "index.html").write_text(
                '<button class="amicro-button">Go</button>',
                encoding="utf-8",
            )
            result = run_script(
                "verify_amicro_style.py",
                str(target),
                "--format",
                "json",
                check=False,
            )
            self.assertEqual(result.returncode, 3)
            report = json.loads(result.stdout)
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("animation-outside-no-preference", codes)

    def test_rejects_absolute_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = run_script(
                "verify_amicro_style.py",
                raw,
                "--output",
                "/tmp/amicro-report.json",
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("must be relative", result.stderr)


class InstallerTests(unittest.TestCase):
    def test_install_update_and_uninstall_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            destination = target / "styles" / "amicro"

            dry_run = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(dry_run.stdout)["status"], "dry-run")
            self.assertFalse(destination.exists())

            apply_result = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(apply_result.stdout)["status"], "ok")
            self.assertTrue((destination / ".amicro-install.json").is_file())

            update = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--update",
                "--format",
                "json",
            )
            actions = {item["action"] for item in json.loads(update.stdout)["plan"]}
            self.assertEqual(actions, {"unchanged"})

            uninstall = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--uninstall",
                "--apply",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(uninstall.stdout)["status"], "ok")
            self.assertFalse((destination / ".amicro-install.json").exists())

    def test_update_blocks_local_drift_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            destination = target / "styles" / "amicro"
            run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--apply",
            )
            (destination / "amicro-tokens.css").write_text(
                "local override\n",
                encoding="utf-8",
            )
            result = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--update",
                "--format",
                "json",
                check=False,
            )
            self.assertEqual(result.returncode, 4)
            self.assertEqual(json.loads(result.stdout)["status"], "blocked")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_uninstall_blocks_managed_symlink_even_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            destination = target / "styles" / "amicro"
            run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--apply",
            )
            managed = destination / "amicro-tokens.css"
            unmanaged = destination / "keep-me.css"
            unmanaged.write_text("do not delete\n", encoding="utf-8")
            managed.unlink()
            managed.symlink_to(unmanaged.name)

            result = run_script(
                "install_style_layer.py",
                str(target),
                "--destination",
                "styles/amicro",
                "--uninstall",
                "--force",
                "--apply",
                "--format",
                "json",
                check=False,
            )
            self.assertEqual(result.returncode, 4)
            self.assertEqual(json.loads(result.stdout)["status"], "blocked")
            self.assertTrue(managed.is_symlink())
            self.assertEqual(unmanaged.read_text(encoding="utf-8"), "do not delete\n")

    def test_rejects_destination_escape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = run_script(
                "install_style_layer.py",
                raw,
                "--destination",
                "../amicro",
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("escapes the target directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
