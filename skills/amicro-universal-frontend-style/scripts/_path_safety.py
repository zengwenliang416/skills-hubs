"""Shared target-containment and atomic-write helpers for Amicro CLI tools."""

from __future__ import annotations

SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared target-containment and atomic-write helpers imported by the Amicro CLIs."

import os
import tempfile
from pathlib import Path


def resolve_inside(target: Path, requested: str, flag: str) -> Path:
    """Resolve a user path inside target, rejecting absolute and symlink escapes."""
    target = target.expanduser().resolve()
    path = Path(requested).expanduser()
    if path.is_absolute():
        raise ValueError(f"{flag} must be relative to the target directory")
    resolved = (target / path).resolve(strict=False)
    try:
        resolved.relative_to(target)
    except ValueError as exc:
        raise ValueError(f"{flag} escapes the target directory") from exc
    if resolved == target:
        raise ValueError(f"{flag} must name a path below the target directory")
    return resolved


def resolve_output_file(target: Path, requested: str) -> Path:
    output = resolve_inside(target, requested, "--output")
    if output.exists() and output.is_dir():
        raise ValueError("--output points to a directory")
    return output


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
