#!/usr/bin/env python3
"""Verify the public Skills Hub from tracked source only."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "npm token": re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
PRIVATE_PATH_FRAGMENTS = (
    "/" + "Users/",
    "/" + "Volumes/",
    "api." + "pftrader.us",
)
DISALLOWED_PACKAGE_PARTS = {
    ".DS_Store",
    "__pycache__",
    "reports",
    "dist",
}


class VerificationError(RuntimeError):
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


def tracked_files() -> list[Path]:
    result = run(["git", "ls-files", "-z"], capture=True)
    return [
        ROOT / item
        for item in result.stdout.split("\0")
        if item
    ]


def scan_public_source(files: list[Path]) -> None:
    findings: list[str] = []
    for path in files:
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        for fragment in PRIVATE_PATH_FRAGMENTS:
            if fragment in text:
                findings.append(f"{relative}: private path or endpoint: {fragment}")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative}: possible {name}")
    if findings:
        raise VerificationError("\n".join(findings))


def parse_npm_json(output: str) -> list[dict]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"npm did not return JSON: {exc}") from exc
    if not isinstance(payload, list) or len(payload) != 1:
        raise VerificationError("npm pack must return exactly one package")
    return payload


def validate_package_files(report: dict, skill_name: str) -> None:
    entries = report.get("files")
    if not isinstance(entries, list) or not entries:
        raise VerificationError(f"{skill_name}: npm package file list is empty")
    for entry in entries:
        package_path = str(entry.get("path", ""))
        parts = set(Path(package_path).parts)
        if parts & DISALLOWED_PACKAGE_PARTS:
            raise VerificationError(
                f"{skill_name}: disallowed npm package path: {package_path}"
            )


def verify_skill(entry: dict) -> dict:
    skill_name = entry.get("name")
    skill_path = ROOT / str(entry.get("path", ""))
    if not skill_name or not skill_path.is_dir() or skill_path.is_symlink():
        raise VerificationError(f"invalid skill entry: {entry}")

    package_path = skill_path / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    if package.get("name") != entry.get("npm"):
        raise VerificationError(f"{skill_name}: catalog npm name mismatch")
    if package.get("version") != entry.get("version"):
        raise VerificationError(f"{skill_name}: catalog version mismatch")

    tests = skill_path / "tests"
    if tests.is_dir():
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_*.py",
            ],
            cwd=skill_path,
        )

    npm_result = run(
        ["npm", "pack", "--dry-run", "--json", "--ignore-scripts"],
        cwd=skill_path,
        capture=True,
    )
    report = parse_npm_json(npm_result.stdout)[0]
    validate_package_files(report, skill_name)
    return {
        "name": skill_name,
        "version": package["version"],
        "npm": package["name"],
        "package_files": report.get("entryCount"),
        "package_bytes": report.get("size"),
    }


def main() -> int:
    run(["git", "diff", "--check"])
    files = tracked_files()
    scan_public_source(files)

    root_tests = ROOT / "tests"
    if root_tests.is_dir():
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_*.py",
            ]
        )

    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    skills = catalog.get("skills")
    if not isinstance(skills, list) or not skills:
        raise VerificationError("catalog.json must contain at least one skill")

    names = [entry.get("name") for entry in skills]
    if len(names) != len(set(names)):
        raise VerificationError("catalog skill names must be unique")

    summary = [verify_skill(entry) for entry in skills]
    print(
        json.dumps(
            {
                "ok": True,
                "tracked_files": len(files),
                "skills": summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, VerificationError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
