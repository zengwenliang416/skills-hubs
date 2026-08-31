#!/usr/bin/env python3
"""Build a tag-bound npm release artifact and evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TAG_PATTERN = re.compile(
    r"^(?P<skill>[a-z0-9][a-z0-9._-]*)@"
    r"(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)$"
)


class ReleaseError(RuntimeError):
    pass


def run(
    command: list[str],
    *,
    cwd: Path = ROOT,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture,
    )


def parse_release_tag(tag: str) -> tuple[str, str]:
    match = TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ReleaseError(
            "release tag must use <skill-name>@<semver>, "
            "for example image-api-workbench@2.0.1"
        )
    return match.group("skill"), match.group("version")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"JSON object required: {path}")
    return value


def require_version(path: Path, version: str) -> None:
    payload = load_json(path)
    if payload.get("version") != version:
        raise ReleaseError(
            f"version mismatch in {path.relative_to(ROOT)}: "
            f"{payload.get('version')} != {version}"
        )


def validate_git(tag: str) -> str:
    head = run(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    ci_sha = os.environ.get("CI_COMMIT_SHA")
    if ci_sha and head != ci_sha:
        raise ReleaseError(f"HEAD {head} does not match CI_COMMIT_SHA {ci_sha}")

    tag_sha = run(["git", "rev-list", "-n", "1", tag], capture=True).stdout.strip()
    if tag_sha != head:
        raise ReleaseError(f"tag {tag} does not resolve to HEAD {head}")

    # Tag-triggered clones may not create a remote-tracking main reference.
    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            "main:refs/remotes/origin/main",
        ]
    )
    run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            head,
            "refs/remotes/origin/main",
        ]
    )
    return head


def build_release(tag: str, output_dir: Path) -> dict:
    skill_name, version = parse_release_tag(tag)
    catalog = load_json(ROOT / "catalog.json")
    entries = [
        entry
        for entry in catalog.get("skills", [])
        if isinstance(entry, dict) and entry.get("name") == skill_name
    ]
    if len(entries) != 1:
        raise ReleaseError(f"catalog must contain exactly one {skill_name} entry")

    entry = entries[0]
    if entry.get("version") != version:
        raise ReleaseError("catalog version does not match release tag")

    skill_path = ROOT / str(entry.get("path", ""))
    if not skill_path.is_dir() or skill_path.is_symlink():
        raise ReleaseError(f"invalid skill path: {skill_path}")

    package = load_json(skill_path / "package.json")
    package_name = str(package.get("name", ""))
    if package_name != entry.get("npm") or package.get("version") != version:
        raise ReleaseError("package.json does not match catalog or release tag")

    require_version(skill_path / "manifest.json", version)
    registry_metadata = (
        skill_path / "registry" / "packages" / f"{skill_name}.json"
    )
    if registry_metadata.exists():
        require_version(registry_metadata, version)

    commit_sha = validate_git(tag)
    run(["npm", "test"], cwd=skill_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    pack = run(
        [
            "npm",
            "pack",
            "--json",
            "--ignore-scripts",
            "--pack-destination",
            str(output_dir),
        ],
        cwd=skill_path,
        capture=True,
    )
    reports = json.loads(pack.stdout)
    if not isinstance(reports, list) or len(reports) != 1:
        raise ReleaseError("npm pack must return exactly one artifact")
    report = reports[0]

    artifact = output_dir / str(report.get("filename", ""))
    if not artifact.is_file():
        raise ReleaseError(f"npm artifact is missing: {artifact}")
    sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    sha_path = output_dir / f"{artifact.name}.sha256"
    sha_path.write_text(f"{sha256}  {artifact.name}\n", encoding="ascii")

    manifest = {
        "schema_version": "1.0",
        "tag": tag,
        "commit_sha": commit_sha,
        "skill": skill_name,
        "package": package_name,
        "version": version,
        "artifact": artifact.name,
        "artifact_bytes": artifact.stat().st_size,
        "sha256": sha256,
        "npm_shasum": report.get("shasum"),
        "npm_integrity": report.get("integrity"),
        "package_files": report.get("entryCount"),
    }
    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    notes = (
        f"# {skill_name} {version}\n\n"
        f"- npm package: `{package_name}@{version}`\n"
        f"- source commit: `{commit_sha}`\n"
        f"- artifact: `{artifact.name}`\n"
        f"- SHA-256: `{sha256}`\n"
    )
    (output_dir / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output-dir", default=".release")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_release(args.tag, ROOT / args.output_dir)
    print(json.dumps({"ok": True, **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, ReleaseError) as exc:
        print(f"release preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
