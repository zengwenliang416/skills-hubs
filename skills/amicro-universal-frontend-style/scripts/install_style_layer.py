#!/usr/bin/env python3
"""Safely install, update, or uninstall the bundled Amicro style layer.

All operations are dry-run by default. Writes require --apply, stay inside the
explicit target, use atomic replacement, and never modify package manifests or
contact the network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _path_safety import atomic_write_text, resolve_inside

SKILL_NAME = "amicro-universal-frontend-style"
SKILL_VERSION = "1.1.0"
INSTALL_MANIFEST = ".amicro-install.json"
DEFAULT_ASSETS = [
    "amicro-tokens.css",
    "amicro-primitives.css",
    "amicro-motion.css",
    "amicro-tokens.json",
    "amicro-tokens.ts",
]
OPTIONAL_ASSETS = ["amicro-motion-presets.ts"]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=str(destination.parent))
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def load_manifest(path: Path, destination: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError("installation manifest must not be a symbolic link")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read installation manifest: {exc}") from exc
    if data.get("skill") != SKILL_NAME or not isinstance(data.get("assets"), list):
        raise ValueError("installation manifest does not describe this Skill")
    for item in data["assets"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
            raise ValueError("installation manifest contains an invalid asset entry")
        resolved = (destination / item["path"]).resolve(strict=False)
        try:
            resolved.relative_to(destination)
        except ValueError as exc:
            raise ValueError("installation manifest contains an escaping asset path") from exc
    return data


def selected_assets(include_presets: bool, existing_manifest: dict[str, Any] | None = None) -> list[str]:
    selected = list(DEFAULT_ASSETS)
    existing_names = {item.get("path") for item in (existing_manifest or {}).get("assets", []) if isinstance(item, dict)}
    if include_presets or any(name in existing_names for name in OPTIONAL_ASSETS):
        selected.extend(OPTIONAL_ASSETS)
    return selected


def make_manifest(destination_relative: str, plan: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "skill": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "installed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "destination": destination_relative,
        "assets": [
            {"path": item["asset"], "sha256": item["source_sha256"]}
            for item in plan
            if item["action"] not in {"remove", "missing"}
        ],
    }


def build_install_plan(assets_dir: Path, destination: Path, selected: list[str], force: bool) -> tuple[list[dict[str, Any]], list[str]]:
    plan: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for name in selected:
        source = assets_dir / name
        dest = destination / name
        source_hash = digest(source)
        action = "create"
        current_hash = ""
        if dest.exists():
            if dest.is_symlink() or dest.is_dir():
                action = "conflict-path"
                conflicts.append(name)
            else:
                current_hash = digest(dest)
                if current_hash == source_hash:
                    action = "unchanged"
                elif force:
                    action = "overwrite"
                else:
                    action = "conflict-existing"
                    conflicts.append(name)
        plan.append({"asset": name, "source": str(source), "destination": str(dest), "action": action, "source_sha256": source_hash, "current_sha256": current_hash})
    return plan, conflicts


def build_update_plan(assets_dir: Path, destination: Path, selected: list[str], manifest: dict[str, Any], force: bool) -> tuple[list[dict[str, Any]], list[str]]:
    old_hashes = {item["path"]: item["sha256"] for item in manifest["assets"]}
    plan: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for name in selected:
        source = assets_dir / name
        dest = destination / name
        source_hash = digest(source)
        old_hash = old_hashes.get(name, "")
        current_hash = ""
        if not dest.exists():
            action = "restore" if old_hash else "create"
        elif dest.is_symlink() or dest.is_dir():
            action = "conflict-path"
            conflicts.append(name)
        else:
            current_hash = digest(dest)
            if current_hash == source_hash:
                action = "unchanged"
            elif old_hash and current_hash == old_hash:
                action = "update"
            elif force:
                action = "overwrite-drift"
            else:
                action = "conflict-local-drift"
                conflicts.append(name)
        plan.append({"asset": name, "source": str(source), "destination": str(dest), "action": action, "source_sha256": source_hash, "previous_sha256": old_hash, "current_sha256": current_hash})
    return plan, conflicts


def build_uninstall_plan(destination: Path, manifest: dict[str, Any], force: bool) -> tuple[list[dict[str, Any]], list[str]]:
    plan: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for item in manifest["assets"]:
        name = item["path"]
        expected_hash = item["sha256"]
        dest = destination / name
        resolved = dest.resolve(strict=False)
        try:
            resolved.relative_to(destination)
        except ValueError:
            action = "conflict-path"
            conflicts.append(name)
            plan.append({"asset": name, "destination": str(dest), "action": action, "expected_sha256": expected_hash, "current_sha256": ""})
            continue
        current_hash = ""
        if dest.is_symlink() or dest.is_dir():
            action = "conflict-path"
            conflicts.append(name)
        elif not dest.exists():
            action = "missing"
        else:
            current_hash = digest(dest)
            if current_hash == expected_hash:
                action = "remove"
            elif force:
                action = "remove-drift"
            else:
                action = "conflict-local-drift"
                conflicts.append(name)
        plan.append({"asset": name, "destination": str(dest), "action": action, "expected_sha256": expected_hash, "current_sha256": current_hash})
    return plan, conflicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or apply a target-scoped Amicro style-layer lifecycle operation.")
    parser.add_argument("target", help="Explicit frontend repository or directory")
    parser.add_argument("--destination", default="src/styles/amicro", help="Relative destination inside target")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--update", action="store_true", help="Update a manifest-managed installation")
    operation.add_argument("--uninstall", action="store_true", help="Remove a manifest-managed installation")
    parser.add_argument("--apply", action="store_true", help="Perform writes; otherwise print a dry-run")
    parser.add_argument("--force", action="store_true", help="Explicitly replace/remove locally drifted managed files")
    parser.add_argument("--include-presets", action="store_true", help="Also manage the TypeScript motion helper")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def emit(result: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"Amicro style layer: {result['status']}")
    print(f"Operation: {result['operation']} ({result['mode']})")
    print(f"Target: {result['target']}")
    print(f"Destination: {result['destination']}")
    for item in result["plan"]:
        print(f"- {item['action']:>21}  {item['asset']}")
    print(result["message"])
    if result["operation"] != "uninstall":
        print("Import order: amicro-tokens.css → amicro-primitives.css → amicro-motion.css")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = Path(args.target).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        print(f"error: target is not a directory: {target}", file=sys.stderr)
        return 2
    try:
        destination = resolve_inside(target, args.destination, "--destination")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    manifest_path = destination / INSTALL_MANIFEST
    manifest: dict[str, Any] | None = None
    if manifest_path.exists():
        try:
            manifest = load_manifest(manifest_path, destination)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    operation = "uninstall" if args.uninstall else ("update" if args.update else "install")
    if operation in {"update", "uninstall"} and manifest is None:
        print(f"error: {operation} requires {manifest_path}; reinstall with --force to adopt a legacy copy", file=sys.stderr)
        return 2

    selected = selected_assets(args.include_presets, manifest)
    missing = [name for name in selected if not (assets_dir / name).is_file()]
    if operation != "uninstall" and missing:
        print(f"error: bundled assets missing: {', '.join(missing)}", file=sys.stderr)
        return 3

    if operation == "install":
        plan, conflicts = build_install_plan(assets_dir, destination, selected, args.force)
    elif operation == "update":
        plan, conflicts = build_update_plan(assets_dir, destination, selected, manifest or {}, args.force)
    else:
        plan, conflicts = build_uninstall_plan(destination, manifest or {}, args.force)

    result: dict[str, Any] = {
        "schema_version": "1.1",
        "skill": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "target": str(target),
        "destination": str(destination),
        "operation": operation,
        "mode": "apply" if args.apply else "dry-run",
        "network_used": False,
        "package_manifest_modified": False,
        "install_manifest": str(manifest_path),
        "plan": plan,
        "conflicts": conflicts,
        "applied": False,
        "import_order": ["amicro-tokens.css", "amicro-primitives.css", "amicro-motion.css"],
    }

    if conflicts:
        result.update(status="blocked", message="Managed files conflict with local content. Review the plan; use --force only when replacement/removal is intended.")
        emit(result, args.format)
        return 4

    if not args.apply:
        result.update(status="dry-run", message="No files were written. Add --apply to perform this exact plan.")
        emit(result, args.format)
        return 0

    if operation == "uninstall":
        for item in plan:
            if item["action"] in {"remove", "remove-drift"}:
                Path(item["destination"]).unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        try:
            destination.rmdir()
        except OSError:
            pass
        result.update(status="ok", applied=True, message="Managed assets and the installation manifest were removed. Unmanaged files were preserved.")
    else:
        for item in plan:
            if item["action"] in {"create", "restore", "overwrite", "update", "overwrite-drift"}:
                atomic_copy(Path(item["source"]), Path(item["destination"]))
        new_manifest = make_manifest(args.destination, plan)
        atomic_write_text(manifest_path, json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n")
        result.update(status="ok", applied=True, message="Assets and their hash manifest are current. Import tokens, primitives, then motion from the normal style entrypoint.")

    emit(result, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
