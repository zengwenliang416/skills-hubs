from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_module("prepare_release", "scripts/release/prepare_release.py")
publish = load_module("publish_npm", "scripts/release/publish_npm.py")


class ReleaseTagTests(unittest.TestCase):
    def test_valid_release_tag(self) -> None:
        self.assertEqual(
            prepare.parse_release_tag("image-api-workbench@2.0.1"),
            ("image-api-workbench", "2.0.1"),
        )

    def test_prerelease_tag(self) -> None:
        self.assertEqual(
            prepare.parse_release_tag("image-api-workbench@2.1.0-rc.1"),
            ("image-api-workbench", "2.1.0-rc.1"),
        )

    def test_invalid_release_tag(self) -> None:
        with self.assertRaises(prepare.ReleaseError):
            prepare.parse_release_tag("v2.0.1")


class DistTagTests(unittest.TestCase):
    def test_stable_uses_latest(self) -> None:
        self.assertEqual(publish.dist_tag("2.0.1"), "latest")

    def test_prerelease_uses_next(self) -> None:
        self.assertEqual(publish.dist_tag("2.1.0-rc.1"), "next")


class GitValidationTests(unittest.TestCase):
    def test_fetches_origin_main_before_ancestry_check(self) -> None:
        commit = "9d082ff61bd33a59c56a7ba5b5f97394d91336f8"
        completed = subprocess.CompletedProcess([], 0, stdout=f"{commit}\n")
        with mock.patch.object(
            prepare,
            "run",
            side_effect=[completed, completed, completed, completed],
        ) as run_mock:
            self.assertEqual(
                prepare.validate_git("amicro-universal-frontend-style@1.1.0"),
                commit,
            )

        self.assertEqual(
            run_mock.call_args_list,
            [
                mock.call(["git", "rev-parse", "HEAD"], capture=True),
                mock.call(
                    [
                        "git",
                        "rev-list",
                        "-n",
                        "1",
                        "amicro-universal-frontend-style@1.1.0",
                    ],
                    capture=True,
                ),
                mock.call(
                    [
                        "git",
                        "fetch",
                        "--no-tags",
                        "origin",
                        "main:refs/remotes/origin/main",
                    ]
                ),
                mock.call(
                    [
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        commit,
                        "refs/remotes/origin/main",
                    ]
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
