#!/usr/bin/env python3
"""Build a side-by-side image review with verifiable metadata."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import struct
from pathlib import Path
from urllib.parse import quote


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_MAX_IMAGE_BYTES = 64 * 1024 * 1024
SCRIPT_INTERFACE = "cli"


class CliError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a bilingual side-by-side image review page.")
    parser.add_argument("--left-dir", required=True)
    parser.add_argument("--right-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="Bilingual Image Contact Sheet")
    parser.add_argument("--left-label", default="Source")
    parser.add_argument("--right-label", default="Localized")
    parser.add_argument("--metadata-out")
    parser.add_argument("--max-image-bytes", type=int, default=DEFAULT_MAX_IMAGE_BYTES)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def list_images(directory: Path) -> list[str]:
    return sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def ensure_output(path: Path, force: bool) -> None:
    if path.is_symlink():
        raise CliError(f"refusing symlink output: {path}")
    if path.exists() and not force:
        raise CliError(f"output exists; pass --force to replace: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def image_info(path: Path, max_bytes: int) -> dict:
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise CliError(f"image exceeds bounded review size: {path}")
    data = path.read_bytes()
    image = detect_image(data)
    if image["format"] == "unknown":
        raise CliError(f"unsupported image format: {path}")
    return {
        "path": str(path),
        "bytes": size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "image": image,
    }


def detect_image(data: bytes) -> dict:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return {
            "format": "png",
            "width": struct.unpack(">I", data[16:20])[0],
            "height": struct.unpack(">I", data[20:24])[0],
        }
    if len(data) >= 4 and data[:2] == b"\xff\xd8":
        return detect_jpeg(data)
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            return {
                "format": "webp",
                "width": 1 + int.from_bytes(data[24:27], "little"),
                "height": 1 + int.from_bytes(data[27:30], "little"),
            }
        return {"format": "webp", "width": None, "height": None}
    return {"format": "unknown", "width": None, "height": None}


def detect_jpeg(data: bytes) -> dict:
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
        if length < 2:
            break
        if marker in {*range(0xC0, 0xC4), *range(0xC5, 0xC8), *range(0xC9, 0xCC), *range(0xCD, 0xD0)}:
            return {
                "format": "jpeg",
                "width": struct.unpack(">H", data[offset + 7 : offset + 9])[0],
                "height": struct.unpack(">H", data[offset + 5 : offset + 7])[0],
            }
        offset += 2 + length
    return {"format": "jpeg", "width": None, "height": None}


def relative_href(out: Path, image_path: Path) -> str:
    relative = os.path.relpath(image_path.resolve(), out.parent.resolve()).replace(os.sep, "/")
    return quote(relative, safe="/")


def size_text(info: dict | None) -> str:
    if info is None:
        return "missing"
    image = info["image"]
    return f"{image.get('width') or '?'} x {image.get('height') or '?'} {image['format']} / {round(info['bytes'] / 1024)} KB"


def render_figure(out: Path, info: dict | None, name: str, label: str) -> str:
    if info is None:
        return (
            f"<figure><figcaption><span>{html.escape(label)}</span><span class=\"badge\">missing</span></figcaption>"
            f"<div class=\"missing\">Missing {html.escape(name)}</div></figure>"
        )
    return (
        "<figure>"
        f"<figcaption><span>{html.escape(label)}</span><span>{html.escape(size_text(info))}</span></figcaption>"
        f"<img src=\"{html.escape(relative_href(out, Path(info['path'])), quote=True)}\" "
        f"alt=\"{html.escape(label + ' ' + name, quote=True)}\">"
        "</figure>"
    )


def render_html(args: argparse.Namespace, out: Path, rows: list[dict], missing_left: list[str], missing_right: list[str]) -> str:
    sections = []
    for row in rows:
        sections.append(
            "<section class=\"pair\">"
            f"<h2>{html.escape(row['name'])}</h2>"
            "<div class=\"grid\">"
            f"{render_figure(out, row['left'], row['name'], args.left_label)}"
            f"{render_figure(out, row['right'], row['name'], args.right_label)}"
            "</div></section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(args.title)}</title>
<style>
:root {{ color-scheme:light; --ink:#14292f; --muted:#607075; --paper:#f7efe1; --line:#d8c9aa; --teal:#0e736f; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.45 Georgia,"Avenir Next",sans-serif; }}
main {{ max-width:1440px; margin:0 auto; padding:32px; }}
h1 {{ margin:0 0 8px; font-size:32px; }}
.summary {{ color:var(--muted); margin-bottom:24px; }}
.pair {{ border-top:1px solid var(--line); padding:24px 0 32px; }}
.pair h2 {{ margin:0 0 12px; font-size:18px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }}
figure {{ margin:0; }}
figcaption {{ display:flex; justify-content:space-between; gap:12px; color:var(--muted); margin:0 0 8px; font-size:13px; }}
img {{ width:100%; height:auto; display:block; background:#fff7e8; border:1px solid var(--line); }}
.missing {{ display:grid; place-items:center; min-height:260px; border:1px dashed #b75b4b; color:#8f3529; background:#fff7ee; }}
.badge {{ color:white; background:var(--teal); border-radius:999px; padding:2px 8px; font-size:12px; }}
@media (max-width:820px) {{ main {{ padding:18px; }} .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main>
<h1>{html.escape(args.title)}</h1>
<div class="summary">{len(rows)} pairs. Missing {html.escape(args.left_label)}: {len(missing_left)}. Missing {html.escape(args.right_label)}: {len(missing_right)}.</div>
{''.join(sections)}
</main></body></html>
"""


def main() -> int:
    args = build_parser().parse_args()
    left_dir = Path(args.left_dir).expanduser()
    right_dir = Path(args.right_dir).expanduser()
    out = Path(args.out).expanduser()
    if not left_dir.is_dir() or not right_dir.is_dir():
        raise CliError("left and right directories must exist")
    if args.max_image_bytes < 1:
        raise CliError("--max-image-bytes must be positive")
    ensure_output(out, args.force)

    left_names = list_images(left_dir)
    right_names = list_images(right_dir)
    names = sorted(set(left_names) | set(right_names))
    missing_left = [name for name in names if name not in left_names]
    missing_right = [name for name in names if name not in right_names]
    if not args.allow_missing and (missing_left or missing_right):
        raise CliError(
            f"image sets differ; missing left: {', '.join(missing_left) or 'none'}; "
            f"missing right: {', '.join(missing_right) or 'none'}"
        )

    rows = []
    for name in names:
        left = left_dir / name
        right = right_dir / name
        rows.append(
            {
                "name": name,
                "left": image_info(left, args.max_image_bytes) if left.exists() else None,
                "right": image_info(right, args.max_image_bytes) if right.exists() else None,
            }
        )
    out.write_text(render_html(args, out, rows, missing_left, missing_right), encoding="utf-8")

    metadata = {
        "ok": True,
        "out": str(out),
        "title": args.title,
        "count": len(rows),
        "missing_left": missing_left,
        "missing_right": missing_right,
        "rows": rows,
    }
    metadata_path = Path(args.metadata_out).expanduser() if args.metadata_out else Path(f"{out}.meta.json")
    ensure_output(metadata_path, args.force)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**metadata, "rows": None, "metadata": str(metadata_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CliError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
