#!/usr/bin/env python3
"""Inspect a frontend target without mutating it or using the network.

The report is intentionally heuristic. It gives an agent a deterministic first
inventory, then the agent must confirm important findings against the code.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from _path_safety import atomic_write_text, resolve_output_file

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "bower_components",
    "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".astro", ".cache",
    "coverage", "vendor", "Pods", "DerivedData", "target", "tmp", "temp", "reports", "registry",
}
TEXT_EXTENSIONS = {
    ".css", ".pcss", ".scss", ".sass", ".less", ".styl", ".html", ".htm",
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".astro",
    ".json", ".md", ".mdx", ".yaml", ".yml", ".toml",
}
IMPORTANT_NAMES = {
    "package.json", "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
    "next.config.ts", "nuxt.config.js", "nuxt.config.ts", "svelte.config.js", "astro.config.mjs",
    "tailwind.config.js", "tailwind.config.cjs", "tailwind.config.ts", "postcss.config.js",
    "components.json", "angular.json", "remix.config.js", "gatsby-config.js", "gatsby-config.ts",
}
PACKAGE_FILES = [
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "deno.json",
]

FRAMEWORK_DEPENDENCIES = {
    "Next.js": {"next"},
    "React": {"react", "react-dom"},
    "Nuxt": {"nuxt"},
    "Vue": {"vue"},
    "SvelteKit": {"@sveltejs/kit"},
    "Svelte": {"svelte"},
    "Astro": {"astro"},
    "Remix": {"@remix-run/react", "@remix-run/node"},
    "Angular": {"@angular/core"},
    "Solid": {"solid-js"},
    "Qwik": {"@builder.io/qwik"},
    "Preact": {"preact"},
    "Gatsby": {"gatsby"},
    "Eleventy": {"@11ty/eleventy"},
}

STYLE_DEPENDENCIES = {
    "Tailwind CSS": {"tailwindcss", "@tailwindcss/vite", "@tailwindcss/postcss"},
    "Sass": {"sass", "node-sass"},
    "Less": {"less"},
    "styled-components": {"styled-components"},
    "Emotion": {"@emotion/react", "@emotion/styled"},
    "Vanilla Extract": {"@vanilla-extract/css"},
    "UnoCSS": {"unocss"},
    "Panda CSS": {"@pandacss/dev"},
    "CSS Modules tooling": {"postcss-modules"},
    "MUI": {"@mui/material"},
    "Chakra UI": {"@chakra-ui/react"},
    "Ant Design": {"antd"},
    "Radix UI": {"@radix-ui/react-dialog", "@radix-ui/react-slot", "radix-ui"},
    "shadcn/ui clues": {"class-variance-authority", "tailwind-merge"},
}

MOTION_DEPENDENCIES = {
    "Motion": {"motion"},
    "Framer Motion": {"framer-motion"},
    "GSAP": {"gsap"},
    "React Spring": {"@react-spring/web", "react-spring"},
    "VueUse Motion": {"@vueuse/motion"},
    "Anime.js": {"animejs"},
    "Auto Animate": {"@formkit/auto-animate"},
    "Lottie": {"lottie-web", "lottie-react"},
}

ENTRYPOINT_NAMES = {
    "main.ts", "main.tsx", "main.js", "main.jsx", "index.tsx", "index.jsx", "app.tsx",
    "App.tsx", "App.jsx", "layout.tsx", "page.tsx", "app.vue", "App.vue", "+layout.svelte",
    "+page.svelte", "index.html", "global.css", "globals.css", "app.css", "style.css", "styles.css",
}


def safe_read(path: Path, max_bytes: int = 1_000_000) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def iter_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink())
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink():
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS and name not in IMPORTANT_NAMES and name not in PACKAGE_FILES:
                continue
            files.append(path)
            if len(files) >= max_files:
                truncated = True
                return files, truncated
    return files, truncated


def dependency_map(package: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        values = package.get(field, {})
        if isinstance(values, dict):
            for key, value in values.items():
                result[str(key)] = str(value)
    return result


def detect_by_dependencies(dependencies: set[str], mapping: dict[str, set[str]]) -> list[str]:
    return [label for label, needles in mapping.items() if dependencies.intersection(needles)]


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def first_paths(paths: Iterable[Path], root: Path, limit: int = 20) -> list[str]:
    return [relative(p, root) for p in sorted(paths)[:limit]]


def inspect(target: Path, max_files: int) -> dict[str, Any]:
    target = target.resolve()
    files, truncated = iter_files(target, max_files)
    rel_names = {relative(path, target): path for path in files}
    suffix_counts = Counter(path.suffix.lower() or "[no extension]" for path in files)

    package_path = target / "package.json"
    package: dict[str, Any] = {}
    package_error = ""
    if package_path.exists():
        try:
            loaded = json.loads(safe_read(package_path))
            if isinstance(loaded, dict):
                package = loaded
            else:
                package_error = "package.json root is not an object"
        except json.JSONDecodeError as exc:
            package_error = f"invalid package.json: {exc}"

    deps_map = dependency_map(package)
    dependencies = set(deps_map)
    frameworks = detect_by_dependencies(dependencies, FRAMEWORK_DEPENDENCIES)
    styling = detect_by_dependencies(dependencies, STYLE_DEPENDENCIES)
    motion = detect_by_dependencies(dependencies, MOTION_DEPENDENCIES)

    # File-based detection fills gaps for repositories without a package manifest.
    if any(path.suffix.lower() == ".vue" for path in files) and "Vue" not in frameworks:
        frameworks.append("Vue")
    if any(path.suffix.lower() == ".svelte" for path in files) and "Svelte" not in frameworks:
        frameworks.append("Svelte")
    if any(path.suffix.lower() == ".astro" for path in files) and "Astro" not in frameworks:
        frameworks.append("Astro")
    if any(path.name.startswith("next.config") for path in files) and "Next.js" not in frameworks:
        frameworks.insert(0, "Next.js")
    if any(path.name.startswith("nuxt.config") for path in files) and "Nuxt" not in frameworks:
        frameworks.insert(0, "Nuxt")

    if any(path.name.endswith(".module.css") or path.name.endswith(".module.scss") for path in files):
        styling.append("CSS Modules")
    if any(path.suffix.lower() in {".scss", ".sass"} for path in files) and "Sass" not in styling:
        styling.append("Sass")
    if any(path.suffix.lower() == ".less" for path in files) and "Less" not in styling:
        styling.append("Less")
    if any("tailwind" in path.name.lower() for path in files) and "Tailwind CSS" not in styling:
        styling.append("Tailwind CSS")

    sample_paths = [p for p in files if p.suffix.lower() in TEXT_EXTENSIONS and p.stat().st_size <= 400_000]
    combined_chunks: list[str] = []
    source_limit = 2_500_000
    total = 0
    for path in sample_paths:
        text = safe_read(path, max_bytes=400_000)
        if not text:
            continue
        remaining = source_limit - total
        if remaining <= 0:
            break
        combined_chunks.append(text[:remaining])
        total += min(len(text), remaining)
    source = "\n".join(combined_chunks)
    lowered = source.lower()

    theme_clues: list[str] = []
    clues = [
        ("prefers-color-scheme", "prefers-color-scheme media query"),
        ("data-theme", "data-theme selector/attribute"),
        ("data-color-mode", "data-color-mode selector/attribute"),
        ("classlist.toggle('dark", "JavaScript dark-class toggle"),
        ("classlist.toggle(\"dark", "JavaScript dark-class toggle"),
        (".dark ", "class-based dark theme"),
        ("color-scheme:", "CSS color-scheme declaration"),
        ("themedprovider", "theme provider clue"),
        ("themeprovider", "theme provider clue"),
        ("next-themes", "next-themes"),
    ]
    for needle, label in clues:
        if needle in lowered and label not in theme_clues:
            theme_clues.append(label)

    motion_code_clues: list[str] = []
    motion_needles = [
        ("prefers-reduced-motion", "reduced-motion CSS"),
        ("usereducedmotion", "reduced-motion hook"),
        ("animatepresence", "mount/unmount animation"),
        ("requestanimationframe", "requestAnimationFrame animation"),
        ("@keyframes", "CSS keyframes"),
        ("transition:", "CSS transitions"),
        ("view-transition", "View Transitions API/CSS"),
    ]
    for needle, label in motion_needles:
        if needle in lowered and label not in motion_code_clues:
            motion_code_clues.append(label)

    css_files = [p for p in files if p.suffix.lower() in {".css", ".pcss", ".scss", ".sass", ".less", ".styl"}]
    component_files = [p for p in files if p.suffix.lower() in {".jsx", ".tsx", ".vue", ".svelte", ".astro"}]
    test_files = [p for p in files if any(marker in p.name.lower() for marker in (".test.", ".spec.", "test_", "_test."))]
    story_files = [p for p in files if ".stories." in p.name.lower()]
    entrypoints = [p for p in files if p.name in ENTRYPOINT_NAMES or p.name in IMPORTANT_NAMES]
    token_candidates = [
        p for p in css_files
        if any(word in p.name.lower() for word in ("token", "theme", "variable", "global", "root", "design"))
    ]

    lockfiles = [name for name in PACKAGE_FILES if (target / name).exists()]
    if (target / "pnpm-workspace.yaml").exists():
        lockfiles.append("pnpm-workspace.yaml")

    package_manager = "unknown"
    if "pnpm-lock.yaml" in lockfiles:
        package_manager = "pnpm"
    elif "yarn.lock" in lockfiles:
        package_manager = "yarn"
    elif "bun.lock" in lockfiles or "bun.lockb" in lockfiles:
        package_manager = "bun"
    elif "package-lock.json" in lockfiles:
        package_manager = "npm"
    elif package.get("packageManager"):
        package_manager = str(package["packageManager"]).split("@", 1)[0]

    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
    available_checks = {
        name: command for name, command in scripts.items()
        if any(token in name.lower() for token in ("format", "lint", "type", "test", "build", "check"))
    }

    risk_notes: list[str] = []
    if truncated:
        risk_notes.append(f"scan truncated at {max_files} eligible files")
    if package_error:
        risk_notes.append(package_error)
    if "Tailwind CSS" in styling and any(v.startswith("4") or "^4" in v or "~4" in v for k, v in deps_map.items() if k == "tailwindcss"):
        risk_notes.append("Tailwind 4 detected; use the existing CSS-first theme conventions rather than a Tailwind 3-only config patch")
    if not theme_clues:
        risk_notes.append("no clear theme mechanism detected; confirm light/dark scope before applying global variables")
    if motion or "CSS transitions" in motion_code_clues or "CSS keyframes" in motion_code_clues:
        if "reduced-motion CSS" not in motion_code_clues and "reduced-motion hook" not in motion_code_clues:
            risk_notes.append("motion exists but no reduced-motion clue was found")

    recommended_path: list[str] = []
    if not styling:
        recommended_path.append("Start with scoped vanilla CSS variables and primitives under a feature root.")
    elif "Tailwind CSS" in styling:
        recommended_path.append("Map Amicro roles to existing CSS variables, then expose only stable roles through the current Tailwind version.")
    elif "CSS Modules" in styling:
        recommended_path.append("Keep tokens at the theme/feature root and component selectors in the existing CSS Modules.")
    elif any(name in styling for name in ("styled-components", "Emotion", "Vanilla Extract")):
        recommended_path.append("Reuse the current theme/provider layer and reference CSS-variable roles instead of introducing a competing theme system.")
    else:
        recommended_path.append("Extend the existing stylesheet/preprocessor conventions and keep the Amicro layer scoped.")

    if motion:
        recommended_path.append(f"Reuse the detected motion stack ({', '.join(motion)}) only for coordinated mount/layout effects; keep simple states in CSS.")
    else:
        recommended_path.append("Use CSS transitions/keyframes first; do not add a motion dependency for simple hover, press, swap, or reveal states.")
    recommended_path.append("Pilot one representative card or control before expanding across the page.")
    recommended_path.append("Run project checks and the bundled verifier, then perform real browser checks for themes, keyboard, touch, and reduced motion.")

    return {
        "schema_version": "1.0",
        "target": str(target),
        "read_only": True,
        "scan": {
            "eligible_files": len(files),
            "truncated": truncated,
            "max_files": max_files,
            "extension_counts": dict(sorted(suffix_counts.items())),
        },
        "package": {
            "name": package.get("name", ""),
            "version": package.get("version", ""),
            "private": package.get("private"),
            "package_manager": package_manager,
            "lockfiles": lockfiles,
            "dependency_count": len(deps_map),
            "available_checks": available_checks,
            "parse_error": package_error,
        },
        "detected": {
            "frameworks": list(dict.fromkeys(frameworks)) or ["No framework confidently detected"],
            "styling": list(dict.fromkeys(styling)) or ["Plain or undetected styling"],
            "motion_libraries": list(dict.fromkeys(motion)) or ["No motion library dependency detected"],
            "motion_code_clues": motion_code_clues,
            "theme_clues": theme_clues,
        },
        "important_files": {
            "entrypoints_and_configs": first_paths(entrypoints, target),
            "token_or_theme_candidates": first_paths(token_candidates, target),
            "stylesheets": first_paths(css_files, target),
            "components": first_paths(component_files, target),
            "tests": first_paths(test_files, target),
            "stories": first_paths(story_files, target),
        },
        "risk_notes": risk_notes,
        "recommended_path": recommended_path,
        "limitations": [
            "Detection is heuristic and must be confirmed against the target code.",
            "This command does not render the UI, run the build, inspect contrast, or verify runtime accessibility.",
            "Generated/vendor directories and symlinks are skipped intentionally.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Frontend Inventory",
        "",
        f"- Target: `{report['target']}`",
        f"- Read-only: `{str(report['read_only']).lower()}`",
        f"- Eligible files scanned: `{report['scan']['eligible_files']}`",
        f"- Scan truncated: `{str(report['scan']['truncated']).lower()}`",
        "",
        "## Detection",
        "",
        f"- Frameworks: {', '.join(report['detected']['frameworks'])}",
        f"- Styling: {', '.join(report['detected']['styling'])}",
        f"- Motion libraries: {', '.join(report['detected']['motion_libraries'])}",
        f"- Motion code clues: {', '.join(report['detected']['motion_code_clues']) or 'none found'}",
        f"- Theme clues: {', '.join(report['detected']['theme_clues']) or 'none found'}",
        "",
        "## Package",
        "",
        f"- Name: `{report['package']['name'] or 'unknown'}`",
        f"- Package manager: `{report['package']['package_manager']}`",
        f"- Dependencies: `{report['package']['dependency_count']}`",
        f"- Lockfiles: {', '.join(report['package']['lockfiles']) or 'none found'}",
    ]
    checks = report["package"]["available_checks"]
    if checks:
        lines.extend(["", "### Available project checks", ""])
        for name, command in checks.items():
            lines.append(f"- `{name}` → `{command}`")

    lines.extend(["", "## Important Files", ""])
    for key, values in report["important_files"].items():
        title = key.replace("_", " ").title()
        lines.append(f"### {title}")
        lines.append("")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- none found")
        lines.append("")

    lines.extend(["## Recommended Adaptation Path", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(report["recommended_path"], 1))
    lines.extend(["", "## Risk Notes", ""])
    lines.extend(f"- {item}" for item in report["risk_notes"] or ["No automatic risk note was produced."])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only frontend stack and style inventory for the Amicro adaptation workflow.")
    parser.add_argument("target", help="Frontend repository or directory to inspect")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", help="Target-relative report path; absolute and escaping paths are rejected")
    parser.add_argument("--max-files", type=int, default=5000, help="Maximum eligible files to inspect (default: 5000)")
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

    report = inspect(target, args.max_files)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
