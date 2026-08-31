#!/usr/bin/env python3
"""Idempotently publish one prepared npm tarball."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PublishError(RuntimeError):
    pass


def npm_view(package: str, version: str) -> str | None:
    result = subprocess.run(
        ["npm", "view", f"{package}@{version}", "dist.integrity", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        value = json.loads(result.stdout)
        return value if isinstance(value, str) else None
    if "E404" in result.stderr or "Not Found" in result.stderr:
        return None
    raise PublishError(f"npm view failed: {result.stderr.strip()}")


def dist_tag(version: str) -> str:
    return "next" if "-" in version else "latest"


def publish(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package = str(manifest.get("package", ""))
    version = str(manifest.get("version", ""))
    expected_integrity = str(manifest.get("npm_integrity", ""))
    artifact = manifest_path.parent / str(manifest.get("artifact", ""))
    if not package or not version or not expected_integrity or not artifact.is_file():
        raise PublishError("release manifest is incomplete")

    existing = npm_view(package, version)
    if existing is not None:
        if existing != expected_integrity:
            raise PublishError(
                f"{package}@{version} already exists with different integrity"
            )
        return {
            "ok": True,
            "status": "already_published",
            "package": package,
            "version": version,
            "integrity": existing,
        }

    if not os.environ.get("NODE_AUTH_TOKEN"):
        raise PublishError("NODE_AUTH_TOKEN is required for a new npm version")

    npmrc = manifest_path.parent / ".npmrc"
    npmrc.write_text(
        "//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}\n",
        encoding="ascii",
    )
    npmrc.chmod(0o600)
    try:
        subprocess.run(
            [
                "npm",
                "publish",
                str(artifact),
                "--access",
                "public",
                "--tag",
                dist_tag(version),
                "--userconfig",
                str(npmrc),
            ],
            cwd=ROOT,
            check=True,
        )
    finally:
        npmrc.unlink(missing_ok=True)

    verified: str | None = None
    for _ in range(12):
        verified = npm_view(package, version)
        if verified is not None:
            break
        time.sleep(5)
    if verified != expected_integrity:
        raise PublishError(
            f"registry verification mismatch: {verified} != {expected_integrity}"
        )
    return {
        "ok": True,
        "status": "published",
        "package": package,
        "version": version,
        "integrity": verified,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = publish(ROOT / args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, PublishError) as exc:
        print(f"npm publication failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
