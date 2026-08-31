from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
