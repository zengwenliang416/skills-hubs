#!/usr/bin/env python3
"""Conservative static checks for an Amicro-inspired frontend adaptation.

The verifier reports code evidence and risky patterns. It checks target-scoped
writes, token parity/contrast when canonical assets are present, and requires
non-essential CSS animation declarations to live under
`prefers-reduced-motion: no-preference`. It still does not replace browser,
assistive-technology, or performance testing.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from _path_safety import atomic_write_text, resolve_output_file

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "dist", "build", "out", ".next", ".nuxt",
    ".svelte-kit", ".astro", "coverage", "vendor", "target", "tmp", "temp", "reports",
    "registry", "evals", "tests", "__pycache__",
}
EXTENSIONS = {".css", ".pcss", ".scss", ".sass", ".less", ".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro"}
STYLE_EXTENSIONS = {".css", ".pcss", ".scss", ".sass", ".less", ".html", ".htm", ".vue", ".svelte", ".astro"}
MARKUP_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro"}
MAX_FILE_BYTES = 1_000_000

DURATION_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)\s*(ms|s)\b", re.I)
TRANSITION_ALL_RE = re.compile(r"\btransition(?:-property)?\s*:\s*all\b", re.I)
TRANSITION_RE = re.compile(r"\btransition\s*:\s*([^;{}]+)", re.I)
ANIMATION_RE = re.compile(r"\banimation(?:-name)?\s*:\s*([^;{}]+)", re.I)
OUTLINE_NONE_RE = re.compile(r"\boutline\s*:\s*(?:none|0)\b", re.I)
LAYOUT_TRANSITION_RE = re.compile(r"\btransition[^;{}]*(?:\btop\b|\bleft\b|\bright\b|\bbottom\b|\bwidth\b|\bheight\b|\bmargin\b|\bpadding\b)[^;{}]*[;}]", re.I | re.S)
INFINITE_RE = re.compile(r"\banimation(?:-iteration-count)?\s*:[^;{}]*\binfinite\b", re.I)
WILL_CHANGE_RE = re.compile(r"\bwill-change\s*:\s*([^;{}]+)", re.I)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    file: str = ""
    line: int | None = None
    evidence: str = ""


def safe_read(path: Path) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def iter_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    files: list[Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink())
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink() or path.suffix.lower() not in EXTENSIONS:
                continue
            files.append(path)
            if len(files) >= max_files:
                return files, True
    return files, False


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def excerpt(text: str, match: re.Match[str], limit: int = 150) -> str:
    return re.sub(r"\s+", " ", match.group(0)).strip()[:limit]


def at_rule_spans(text: str, rule: str = "@media") -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    lower = text.lower()
    cursor = 0
    while True:
        start = lower.find(rule, cursor)
        if start < 0:
            break
        brace = text.find("{", start)
        if brace < 0:
            break
        prelude = lower[start:brace]
        depth = 1
        index = brace + 1
        quote = ""
        while index < len(text) and depth:
            char = text[index]
            if quote:
                if char == quote and text[index - 1] != "\\":
                    quote = ""
            elif char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        if depth == 0:
            spans.append((start, index, prelude))
            cursor = index
        else:
            break
    return spans


def inside(position: int, spans: Iterable[tuple[int, int, str]], phrase: str) -> bool:
    phrase = phrase.lower()
    return any(start <= position < end and phrase in prelude for start, end, prelude in spans)


def css_animation_safety(path: Path, text: str, target: Path) -> list[Finding]:
    if path.suffix.lower() not in STYLE_EXTENSIONS:
        return []
    spans = at_rule_spans(text)
    findings: list[Finding] = []
    for match in ANIMATION_RE.finditer(text):
        value = match.group(1).strip().lower()
        if value.startswith("none") or inside(match.start(), spans, "prefers-reduced-motion: no-preference"):
            continue
        if inside(match.start(), spans, "prefers-reduced-motion: reduce"):
            continue
        findings.append(Finding(
            "fail",
            "animation-outside-no-preference",
            "Non-essential CSS animation is declared outside prefers-reduced-motion: no-preference; a later low-specificity override may not stop it.",
            rel(path, target),
            line_number(text, match.start()),
            excerpt(text, match),
        ))
    for match in TRANSITION_RE.finditer(text):
        value = match.group(1).strip().lower()
        if value.startswith("none") or inside(match.start(), spans, "prefers-reduced-motion: no-preference") or inside(match.start(), spans, "prefers-reduced-motion: reduce"):
            continue
        findings.append(Finding(
            "warn",
            "transition-outside-no-preference",
            "Transition is active by default. Confirm an equal-or-higher-specificity reduced-motion rule disables or shortens it.",
            rel(path, target),
            line_number(text, match.start()),
            excerpt(text, match),
        ))
    return findings


def parse_hex(value: str) -> tuple[float, float, float] | None:
    value = value.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        value = "#" + "".join(char * 2 for char in value[1:])
    if not re.fullmatch(r"#[0-9a-f]{6}", value):
        return None
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))  # type: ignore[return-value]


def luminance(rgb: tuple[float, float, float]) -> float:
    values = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in rgb]
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast(foreground: str, background: str) -> float | None:
    fg = parse_hex(foreground)
    bg = parse_hex(background)
    if fg is None or bg is None:
        return None
    light, dark = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def find_named_file(target: Path, name: str) -> Path | None:
    direct = target / "assets" / name
    if direct.is_file() and not direct.is_symlink():
        return direct
    for current, dirs, names in os.walk(target, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink())
        if name in names:
            candidate = Path(current) / name
            if candidate.is_file() and not candidate.is_symlink():
                return candidate
    return None


def token_checks(target: Path) -> tuple[list[dict[str, str]], list[Finding], dict[str, Any]]:
    checks: list[dict[str, str]] = []
    findings: list[Finding] = []
    signals: dict[str, Any] = {"canonical_tokens": False, "token_parity": None, "contrast_matrix": None}
    source_path = find_named_file(target, "amicro-tokens.json")
    if source_path is None:
        return checks, findings, signals
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        findings.append(Finding("fail", "invalid-token-source", "amicro-tokens.json could not be parsed.", rel(source_path, target)))
        return checks, findings, signals
    variables = data.get("variables")
    if not isinstance(variables, list):
        findings.append(Finding("fail", "incomplete-token-source", "Canonical token source does not contain the complete variables array.", rel(source_path, target)))
        return checks, findings, signals
    items = [item for item in variables if isinstance(item, dict) and isinstance(item.get("name"), str)]
    signals["canonical_tokens"] = True

    css_path = source_path.with_name("amicro-tokens.css")
    ts_path = source_path.with_name("amicro-tokens.ts")
    parity_errors: list[str] = []
    css_text = safe_read(css_path)
    ts_text = safe_read(ts_path)
    for item in items:
        name = item["name"]
        value = str(item.get("value", ""))
        occurrences = [match.group(1).strip() for match in re.finditer(re.escape(name) + r"\s*:\s*([^;]+);", css_text)]
        if not occurrences or occurrences[0] != value:
            parity_errors.append(f"{name}: light CSS mismatch")
        dark = item.get("dark")
        if dark is not None and str(dark) not in occurrences[1:]:
            parity_errors.append(f"{name}: dark CSS mismatch")
        expected_light_line = f'{json.dumps(name)}: {json.dumps(value, ensure_ascii=False)}'
        if expected_light_line not in ts_text:
            parity_errors.append(f"{name}: TypeScript light mismatch")
        if dark is not None:
            expected_dark_line = f'{json.dumps(name)}: {json.dumps(str(dark), ensure_ascii=False)}'
            if expected_dark_line not in ts_text:
                parity_errors.append(f"{name}: TypeScript dark mismatch")
    if parity_errors:
        signals["token_parity"] = False
        checks.append({"name": "Canonical token parity", "status": "fail", "evidence": f"{len(parity_errors)} JSON/CSS/TypeScript mismatches.", "recommendation": "Run scripts/generate_token_assets.py <skill-dir> --write, then commit all generated artifacts."})
        findings.extend(Finding("fail", "token-parity", message, rel(source_path, target)) for message in parity_errors[:12])
    else:
        signals["token_parity"] = True
        checks.append({"name": "Canonical token parity", "status": "pass", "evidence": f"{len(items)} canonical variables match CSS and TypeScript artifacts.", "recommendation": ""})

    by_name = {item["name"]: item for item in items}
    contrast_rows: list[dict[str, Any]] = []
    failures = 0
    for theme, value_key in (("light", "value"), ("dark", "dark")):
        muted_item = by_name.get("--amicro-text-muted", {})
        muted = muted_item.get(value_key, muted_item.get("value") if theme == "light" else None)
        for role in ("page", "surface", "stage"):
            background_item = by_name.get(f"--amicro-{role}", {})
            background = background_item.get(value_key, background_item.get("value") if theme == "light" else None)
            if not isinstance(muted, str) or not isinstance(background, str):
                continue
            ratio = contrast(muted, background)
            if ratio is None:
                continue
            passed = ratio >= 4.5
            failures += 0 if passed else 1
            contrast_rows.append({"theme": theme, "foreground": muted, "background_role": role, "background": background, "ratio": round(ratio, 3), "pass": passed})
    signals["contrast_matrix"] = contrast_rows
    if contrast_rows and failures:
        checks.append({"name": "Muted text contrast", "status": "fail", "evidence": f"{failures}/{len(contrast_rows)} small-text combinations fall below 4.5:1.", "recommendation": "Darken/lighten --amicro-text-muted or change its supported background roles."})
        for row in contrast_rows:
            if not row["pass"]:
                findings.append(Finding("fail", "muted-contrast", f"{row['theme']} muted text on {row['background_role']} is {row['ratio']}:1, below 4.5:1.", rel(source_path, target)))
    elif contrast_rows:
        checks.append({"name": "Muted text contrast", "status": "pass", "evidence": f"{len(contrast_rows)}/{len(contrast_rows)} light/dark page/surface/stage combinations meet 4.5:1.", "recommendation": ""})
    return checks, findings, signals


def check(target: Path, max_files: int) -> dict[str, Any]:
    files, truncated = iter_files(target, max_files)
    texts: dict[Path, str] = {path: safe_read(path) for path in files}
    combined = "\n".join(texts.values())
    lower = combined.lower()
    findings: list[Finding] = []

    token_count = combined.count("--amicro-")
    has_asset_import = any(name in lower for name in ("amicro-tokens.css", "amicro-primitives.css", "amicro-motion.css"))
    has_motion = any(clue in lower for clue in ("animation:", "transition:", "animatepresence", "motion.", "motion(", "requestanimationframe", "view-transition"))
    has_interactive = any(clue in lower for clue in ("<button", "<a ", "onclick", "@click", "on:click", "role=\"button", "role='button"))
    has_focus_visible = ":focus-visible" in lower or "focus-visible:" in lower or "focusvisible" in lower
    has_reduced_motion = "prefers-reduced-motion: reduce" in lower or "usereducedmotion" in lower or "prefersreducedmotion" in lower
    has_light = any(clue in lower for clue in ("data-amicro-theme=\"light", "data-amicro-theme='light")) or re.search(r"--amicro-page\s*:\s*#f8f9fa\b", lower) is not None or re.search(r"color-scheme\s*:\s*light\b", lower) is not None
    has_dark = any(clue in lower for clue in ("data-amicro-theme=\"dark", "data-amicro-theme='dark", ".dark ")) or re.search(r"--amicro-page\s*:\s*#121212\b", lower) is not None or re.search(r"color-scheme\s*:\s*dark\b", lower) is not None
    has_responsive = any(clue in lower for clue in ("@media", "@container", "clamp(", "minmax(", "auto-fit", "auto-fill"))
    has_pointer_guard = re.search(r"(?:hover|pointer)\s*:\s*(?:hover|fine|coarse)\b", lower) is not None

    for path, text in texts.items():
        findings.extend(css_animation_safety(path, text, target))
        if not text:
            continue
        path_rel = rel(path, target)
        for match in TRANSITION_ALL_RE.finditer(text):
            findings.append(Finding("warn", "transition-all", "Avoid transition: all; list intended properties.", path_rel, line_number(text, match.start()), excerpt(text, match)))
        for match in OUTLINE_NONE_RE.finditer(text):
            findings.append(Finding("warn", "outline-removed", "Outline is removed; verify an equal or stronger focus replacement exists.", path_rel, line_number(text, match.start()), excerpt(text, match)))
        for match in LAYOUT_TRANSITION_RE.finditer(text):
            findings.append(Finding("warn", "layout-property-motion", "Layout-property transition may cause layout work; prefer transform/opacity where possible.", path_rel, line_number(text, match.start()), excerpt(text, match)))
        spans = at_rule_spans(text) if path.suffix.lower() in STYLE_EXTENSIONS else []
        for match in INFINITE_RE.finditer(text):
            if inside(match.start(), spans, "prefers-reduced-motion: no-preference") and has_reduced_motion:
                continue
            findings.append(Finding("warn", "infinite-animation", "Infinite animation found outside a proven reduced-motion gate.", path_rel, line_number(text, match.start()), excerpt(text, match)))
        for match in WILL_CHANGE_RE.finditer(text):
            findings.append(Finding("info", "will-change", "will-change found; keep it temporary and narrowly scoped.", path_rel, line_number(text, match.start()), match.group(1).strip()[:150]))
        for match in DURATION_RE.finditer(text):
            number = float(match.group(1))
            milliseconds = number * (1000 if match.group(2).lower() == "s" else 1)
            context = text[max(0, match.start() - 110):match.end() + 110].lower()
            if milliseconds > 900 and any(keyword in context for keyword in ("transition", "animation", "duration")) and "infinite" not in context:
                findings.append(Finding("warn", "long-motion", f"Motion value {match.group(0)} exceeds the usual 900ms task-UI ceiling.", path_rel, line_number(text, match.start()), excerpt(text, match)))
        if path.suffix.lower() in MARKUP_EXTENSIONS:
            for marker in re.finditer(r"amicro-text-swap", text):
                window = text[marker.start():marker.start() + 900]
                if window.count("data-active") >= 2 and not re.search(r"data-active=[\"']false[\"'][^>]*\bhidden\b", window, re.I):
                    findings.append(Finding("fail", "text-swap-accessible-name", "A multi-node text swap can expose both labels. Use one text node or hide inactive labels with hidden/aria-hidden.", path_rel, line_number(text, marker.start()), "amicro-text-swap with multiple data-active labels"))
            if "examples/" in path_rel and "amicro-card" in text and not ("data-amicro-root" in text or re.search(r"class(?:Name)?=[\"'][^\"']*\bamicro\b", text)):
                findings.append(Finding("warn", "unscoped-example", "Example uses Amicro primitives without an explicit token scope root.", path_rel, 1))

    unsafe_animation_count = sum(1 for item in findings if item.code == "animation-outside-no-preference")
    checks: list[dict[str, str]] = []

    def add_check(name: str, status: str, evidence: str, recommendation: str = "") -> None:
        checks.append({"name": name, "status": status, "evidence": evidence, "recommendation": recommendation})

    if token_count >= 8 or has_asset_import:
        add_check("Amicro token/style layer", "pass", f"Found {token_count} --amicro-* references; bundled import clue={has_asset_import}.")
    else:
        add_check("Amicro token/style layer", "warn", f"Only {token_count} --amicro-* references and no bundled import clue.", "Map page/surface/stage/text/border/accent roles through scoped variables or the bundled assets.")

    if not has_interactive or has_focus_visible:
        add_check("Visible keyboard focus", "pass", "No interactive clue found or :focus-visible evidence exists.")
    else:
        add_check("Visible keyboard focus", "fail", "Interactive elements found without a clear focus-visible rule.", "Add a high-contrast :focus-visible treatment and ensure overflow does not clip it.")
        findings.append(Finding("fail", "missing-focus-visible", "Interactive code exists but no focus-visible clue was found."))

    if not has_motion:
        add_check("Reduced motion", "pass", "No motion clue found.")
    elif unsafe_animation_count:
        add_check("Reduced motion", "fail", f"Found {unsafe_animation_count} animation declarations outside no-preference gating.", "Move non-essential animation declarations into @media (prefers-reduced-motion: no-preference); retain a reduce emergency stop.")
    elif has_reduced_motion or "prefers-reduced-motion: no-preference" in lower:
        add_check("Reduced motion", "pass", "Animation declarations are gated and a reduced/no-preference policy is present.")
    else:
        add_check("Reduced motion", "fail", "Motion exists without a reduced-motion policy.", "Gate non-essential motion with prefers-reduced-motion and preserve static state.")
        findings.append(Finding("fail", "missing-reduced-motion", "Motion code exists without a reduced-motion clue."))

    if has_light and has_dark:
        add_check("Theme coverage", "pass", "Both light and dark Amicro/theme clues were found.")
    else:
        missing = "light" if not has_light else "dark"
        add_check("Theme coverage", "warn", f"No clear {missing}-theme Amicro clue found.", "Confirm the requested theme scope; add both only when the target supports both.")

    add_check("Responsive clues", "pass" if has_responsive else "warn", "Responsive CSS or fluid sizing clue found." if has_responsive else "No media/container/fluid sizing clue found.", "" if has_responsive else "Check 320, 360, 768, and desktop widths; avoid fixed demo-card sizing.")
    add_check("Pointer capability guard", "pass" if (not has_motion or has_pointer_guard) else "warn", "No hover motion clue or pointer/hover capability guard exists." if (not has_motion or has_pointer_guard) else "Motion exists without a clear hover/pointer guard.", "" if (not has_motion or has_pointer_guard) else "Keep essential states touch-visible and gate hover travel to fine pointers.")

    token_extra_checks, token_findings, token_signals = token_checks(target)
    checks.extend(token_extra_checks)
    findings.extend(token_findings)

    if truncated:
        findings.append(Finding("info", "scan-truncated", f"Scan stopped at {max_files} files; results may be incomplete."))

    severity_counts = {"fail": 0, "warn": 0, "info": 0}
    for item in findings:
        severity_counts[item.severity] = severity_counts.get(item.severity, 0) + 1
    failed_checks = sum(1 for item in checks if item["status"] == "fail")
    warning_checks = sum(1 for item in checks if item["status"] == "warn")
    status = "fail" if failed_checks or severity_counts["fail"] else ("pass_with_warnings" if warning_checks or severity_counts["warn"] else "pass")

    return {
        "schema_version": "1.1",
        "target": str(target),
        "status": status,
        "static_only": True,
        "scan": {"files": len(files), "truncated": truncated, "max_files": max_files, "excluded_directories": sorted(SKIP_DIRS)},
        "signals": {
            "amicro_token_references": token_count,
            "bundled_asset_import": has_asset_import,
            "motion": has_motion,
            "interactive": has_interactive,
            "focus_visible": has_focus_visible,
            "reduced_motion": has_reduced_motion,
            "animation_declarations_outside_no_preference": unsafe_animation_count,
            "light_theme": has_light,
            "dark_theme": has_dark,
            "responsive": has_responsive,
            "pointer_guard": has_pointer_guard,
            **token_signals,
        },
        "checks": checks,
        "findings": [asdict(item) for item in findings],
        "finding_counts": severity_counts,
        "manual_checks_required": [
            "Render and inspect 320, 360, 768, and desktop layouts without hiding overflow defects.",
            "Verify keyboard order, focus behavior, touch interaction, and screen-reader names/states.",
            "Verify text, icon, focus, and semantic contrast in each supported theme.",
            "Enable reduced motion, trigger every animated state, and inspect document.getAnimations().",
            "Check runtime smoothness, layout shift, clipping, stacking context, and horizontal overflow.",
            "Exercise loading, empty, success, error, disabled, long-content, RTL, and no-JavaScript states as relevant.",
        ],
        "honesty_boundary": "This report is a conservative static scan. Token parity and simple contrast can be proven from bundled sources; visual quality, runtime accessibility, full CSS cascade behavior, and performance still require real browser checks.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Amicro Style Verification",
        "",
        f"- Target: `{report['target']}`",
        f"- Status: **{report['status']}**",
        f"- Static-only: `{str(report['static_only']).lower()}`",
        f"- Files scanned: `{report['scan']['files']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        evidence = item["evidence"].replace("|", "\\|")
        lines.append(f"| {item['name']} | {item['status']} | {evidence} |")
        if item.get("recommendation"):
            recommendation = item["recommendation"].replace("|", "\\|")
            lines.append(f"| ↳ recommendation |  | {recommendation} |")
    lines.extend(["", "## Findings", ""])
    if report["findings"]:
        for item in report["findings"]:
            location = f" `{item['file']}:{item.get('line') or 1}`" if item.get("file") else ""
            evidence = f" — `{item['evidence']}`" if item.get("evidence") else ""
            lines.append(f"- **{item['severity']} / {item['code']}**{location}: {item['message']}{evidence}")
    else:
        lines.append("- No risky static pattern was detected by this rule set.")
    lines.extend(["", "## Manual Checks Still Required", ""])
    lines.extend(f"- {item}" for item in report["manual_checks_required"])
    lines.extend(["", f"> {report['honesty_boundary']}", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conservative static Amicro style, motion-safety, token, and integration checks.")
    parser.add_argument("target", help="Explicit frontend repository or directory to scan")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", help="Target-relative report path; absolute and escaping paths are rejected")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--strict", action="store_true", help="Return non-zero for warnings as well as failures")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = Path(args.target).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        print(f"error: target is not a directory: {target}", file=sys.stderr)
        return 2
    if args.max_files < 1:
        print("error: --max-files must be positive", file=sys.stderr)
        return 2
    report = check(target, args.max_files)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_markdown(report)
    if args.output:
        try:
            output = resolve_output_file(target, args.output)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        atomic_write_text(output, text)
    else:
        sys.stdout.write(text)
    if report["status"] == "fail":
        return 3
    if args.strict and report["status"] == "pass_with_warnings":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
