#!/usr/bin/env python3
"""Generate/check CSS and TypeScript token artifacts from amicro-tokens.json.

The JSON file is the canonical public token source. The command is read-only by
default; pass --write to update generated files inside the selected Skill root.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCOPE = ":where(.amicro, [data-amicro-scope], [data-amicro-root])"


def load_source(skill_dir: Path) -> dict[str, Any]:
    source_path = skill_dir / "assets" / "amicro-tokens.json"
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read canonical token source: {source_path}: {exc}") from exc
    variables = data.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError("canonical token source must contain a non-empty variables array")
    seen: set[str] = set()
    for item in variables:
        if not isinstance(item, dict):
            raise ValueError("each token variable must be an object")
        name = item.get("name")
        value = item.get("value")
        if not isinstance(name, str) or not name.startswith("--amicro-"):
            raise ValueError(f"invalid token variable name: {name!r}")
        if name in seen:
            raise ValueError(f"duplicate token variable: {name}")
        if not isinstance(value, (str, int, float)):
            raise ValueError(f"token {name} has an unsupported value")
        seen.add(name)
    return data


def render_css(data: dict[str, Any]) -> str:
    variables: list[dict[str, Any]] = data["variables"]
    dark = [item for item in variables if "dark" in item]
    lines = [
        "/*",
        " * Amicro Universal Frontend Style — generated scoped design tokens",
        " * Canonical source: amicro-tokens.json. Run generate_token_assets.py --check.",
        " * Opt in with class=\"amicro\", data-amicro-scope, or data-amicro-root.",
        " */",
        "",
        f"{SCOPE} {{",
        "  color-scheme: light;",
        "",
    ]
    for item in variables:
        lines.append(f"  {item['name']}: {item['value']};")
    lines.extend(["}", "", f"{SCOPE}[data-amicro-theme=\"dark\"],", f":where([data-amicro-theme=\"dark\"]) {SCOPE},", f":where(.amicro-theme-dark) {SCOPE} {{", "  color-scheme: dark;"])
    for item in dark:
        lines.append(f"  {item['name']}: {item['dark']};")
    lines.extend(["}", "", "@media (prefers-color-scheme: dark) {", f"  {SCOPE}[data-amicro-theme=\"auto\"] {{", "    color-scheme: dark;"])
    for item in dark:
        lines.append(f"    {item['name']}: {item['dark']};")
    lines.extend([
        "  }",
        "}",
        "",
        "@media (forced-colors: active) {",
        f"  {SCOPE} {{",
        "    --amicro-border: CanvasText;",
        "    --amicro-border-strong: Highlight;",
        "    --amicro-focus: Highlight;",
        "  }",
        "}",
        "",
    ])
    return "\n".join(lines)


def ts_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def render_ts(data: dict[str, Any]) -> str:
    variables: list[dict[str, Any]] = data["variables"]
    dark = [item for item in variables if "dark" in item]
    lines = [
        "/** Generated from amicro-tokens.json. Do not edit by hand. */",
        "export const AMICRO_TOKENS_LIGHT = {",
    ]
    for item in variables:
        lines.append(f"  {json.dumps(item['name'])}: {ts_string(item['value'])},")
    lines.extend(["} as const;", "", "export const AMICRO_TOKENS_DARK = {"])
    for item in dark:
        lines.append(f"  {json.dumps(item['name'])}: {ts_string(item['dark'])},")
    lines.extend(["} as const;", "", "export const AMICRO_MOTION_SPRINGS = " + json.dumps(data.get("motion_springs", {}), ensure_ascii=False, indent=2) + " as const;", "", "export type AmicroTokenName = keyof typeof AMICRO_TOKENS_LIGHT;", ""])
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    import os
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check or generate Amicro CSS/TypeScript token artifacts from canonical JSON.")
    parser.add_argument("skill_dir", help="Explicit Amicro Skill directory")
    parser.add_argument("--write", action="store_true", help="Write generated artifacts; default is read-only check")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
        print(f"error: not an Amicro Skill directory: {skill_dir}", file=sys.stderr)
        return 2
    try:
        data = load_source(skill_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    expected = {
        skill_dir / "assets" / "amicro-tokens.css": render_css(data),
        skill_dir / "assets" / "amicro-tokens.ts": render_ts(data),
    }
    drift: list[str] = []
    for path, text in expected.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current != text:
            drift.append(path.relative_to(skill_dir).as_posix())
            if args.write:
                atomic_write(path, text)

    if drift and not args.write:
        print("token artifact drift: " + ", ".join(drift), file=sys.stderr)
        return 1
    if args.write:
        print("updated: " + (", ".join(drift) if drift else "no files; artifacts already current"))
    else:
        print(f"ok: {len(data['variables'])} canonical variables match CSS and TypeScript artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
