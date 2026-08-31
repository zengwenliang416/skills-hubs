#!/usr/bin/env python3
"""Reproducible OpenAI Images API client for compatible gateways."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import struct
import sys
import time
import urllib.error
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen


VERSION = "2.0.0"
SCRIPT_INTERFACE = "cli"
DEFAULT_BASE_URL = "http://127.0.0.1:3000/v1"
DEFAULT_TOKEN_FILE = Path("/root/.openclaw/new-api.token")
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_TIMEOUT_SECONDS = 1200
DEFAULT_MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
MAX_PROMPT_CHARS = 32_000
MAX_INPUT_IMAGES = 16
MAX_INPUT_BYTES = 50 * 1024 * 1024
KNOWN_IMAGE_FORMATS = {"png", "jpeg", "webp"}
RESERVED_PARAMS = {
    "model",
    "prompt",
    "size",
    "quality",
    "n",
    "background",
    "output_format",
    "output_compression",
    "moderation",
    "input_fidelity",
    "stream",
    "partial_images",
    "response_format",
}

SIZE_PRESETS = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "hd-16:9": "1536x864",
    "2k-16:9": "2560x1440",
    "2k-9:16": "1440x2560",
    "4k-16:9": "3840x2160",
    "4k-9:16": "2160x3840",
    "ultrawide": "3840x1648",
}

MODEL_PROFILES = {
    "gpt-image-2": {
        "family": "gpt-image-2",
        "status": "current",
        "supports_transparency": True,
        "supports_streaming": True,
        "supports_flexible_size": True,
        "input_fidelity": "always-high",
    },
    "gpt-image-1.5": {
        "family": "gpt-image-1.5",
        "status": "deprecated",
        "shutdown": "2026-12-01",
        "replacement": "gpt-image-2",
        "supports_transparency": True,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "low-or-high",
    },
    "chatgpt-image-latest": {
        "family": "chatgpt-image-latest",
        "status": "deprecated",
        "shutdown": "2026-12-01",
        "replacement": "gpt-image-2",
        "supports_transparency": True,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "provider-defined",
    },
    "gpt-image-1": {
        "family": "gpt-image-1",
        "status": "older",
        "supports_transparency": True,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "low-or-high",
    },
    "gpt-image-1-mini": {
        "family": "gpt-image-1-mini",
        "status": "deprecated",
        "shutdown": "2026-12-01",
        "replacement": "gpt-image-2",
        "supports_transparency": True,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "low-or-high",
    },
    "dall-e-2": {
        "family": "dall-e-2",
        "status": "retired",
        "shutdown": "2026-05-12",
        "replacement": "gpt-image-2",
        "supports_transparency": False,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "unsupported",
    },
    "dall-e-3": {
        "family": "dall-e-3",
        "status": "retired",
        "shutdown": "2026-05-12",
        "replacement": "gpt-image-2",
        "supports_transparency": False,
        "supports_streaming": False,
        "supports_flexible_size": False,
        "input_fidelity": "unsupported",
    },
}


class CliError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate, edit, probe, and verify images through OpenAI Images API compatible endpoints."
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--out")
    parser.add_argument("--mode", choices=("generation", "edit"))
    parser.add_argument("--edit", action="store_true")
    parser.add_argument("--input-image", "--image", "--reference-image", action="append", default=[])
    parser.add_argument("--mask")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--size", default="auto")
    parser.add_argument("--quality", choices=("auto", "low", "medium", "high"), default="auto")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--background", choices=("auto", "opaque", "transparent"), default="auto")
    parser.add_argument("--output-format", choices=("png", "jpeg", "webp"), default="png")
    parser.add_argument("--output-compression", type=int)
    parser.add_argument("--moderation", choices=("auto", "low"), default="auto")
    parser.add_argument("--input-fidelity", choices=("low", "high"))
    parser.add_argument("--response-format")
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--partial-images", type=int, default=0)
    parser.add_argument("--partial-dir")
    parser.add_argument(
        "--base-url",
        default=first_env(
            "IMAGE_API_BASE_URL",
            "NEWAPI_IMAGE_BASE_URL",
            "NEWAPI_BASE_URL",
            "OPENAI_BASE_URL",
            "OPENAI_API_BASE",
        )
        or DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "--token-file",
        default=first_env("IMAGE_API_TOKEN_FILE", "NEWAPI_TOKEN_FILE")
        or (str(DEFAULT_TOKEN_FILE) if DEFAULT_TOKEN_FILE.exists() else ""),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=number_from_env("IMAGE_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
    )
    parser.add_argument("--max-download-bytes", type=int, default=DEFAULT_MAX_DOWNLOAD_BYTES)
    parser.add_argument("--metadata-out")
    parser.add_argument("--include-prompt-preview", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-deprecated-model", action="store_true")
    parser.add_argument("--allow-retired-model", action="store_true")
    parser.add_argument("--allow-provider-extensions", action="store_true")
    parser.add_argument("--allow-insecure-localhost", action="store_true")
    parser.add_argument("--allow-insecure-token-file", action="store_true")
    parser.add_argument("--strict-model-profile", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-size-presets", action="store_true")
    parser.add_argument("--list-model-profiles", action="store_true")
    parser.add_argument("--list-remote-models", action="store_true")
    return parser


def first_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


def number_from_env(name: str, fallback: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        return fallback
    return value if value > 0 else fallback


def load_env_defaults() -> None:
    original = set(os.environ)
    for path in (Path.home() / ".content-skills/.env", Path.cwd() / ".content-skills/.env"):
        if not path.exists():
            continue
        for key, value in parse_env_file(path).items():
            if key not in original:
                os.environ[key] = value


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value)
        values[key] = value
    return values


def resolve_model_profile(model: str) -> tuple[dict[str, Any] | None, list[str]]:
    profile = MODEL_PROFILES.get(model)
    if profile is None and model.startswith("gpt-image-2-"):
        profile = {**MODEL_PROFILES["gpt-image-2"], "snapshot": model}
    warnings: list[str] = []
    if profile is None:
        warnings.append("unverified-model-profile")
    return profile, warnings


def resolve_size(value: str) -> str:
    return SIZE_PRESETS.get(value, value)


def parse_param(value: str) -> tuple[str, Any]:
    if "=" not in value:
        raise CliError("--param must be KEY=VALUE")
    key, raw = value.split("=", 1)
    key = key.strip()
    if not key:
        raise CliError("--param key is empty")
    if key in RESERVED_PARAMS:
        raise CliError(f"--param cannot override first-class field: {key}")
    raw = raw.strip()
    if raw in {"true", "false", "null"}:
        return key, {"true": True, "false": False, "null": None}[raw]
    if re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
        return key, float(raw) if "." in raw else int(raw)
    if raw.startswith(("{", "[")):
        try:
            return key, json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CliError(f"invalid JSON value for --param {key}: {exc.msg}") from exc
    return key, raw


def model_is_known_gpt(profile: dict[str, Any] | None) -> bool:
    return bool(profile and str(profile.get("family", "")).startswith(("gpt-image", "chatgpt-image")))


def validate_size(size: str, profile: dict[str, Any] | None, allow_extensions: bool) -> list[str]:
    warnings: list[str] = []
    if size == "auto":
        return warnings
    match = re.fullmatch(r"(\d{2,5})x(\d{2,5})", size)
    if not match:
        raise CliError("--size must be auto, WIDTHxHEIGHT, or a known preset")
    width, height = map(int, match.groups())
    family = profile.get("family") if profile else ""
    if family == "gpt-image-2":
        failures = []
        if width < 512 or height < 512 or width > 3840 or height > 3840:
            failures.append("each edge must be 512..3840")
        if width % 16 or height % 16:
            failures.append("both edges must be multiples of 16")
        pixels = width * height
        if pixels < 655_360 or pixels > 8_294_400:
            failures.append("total pixels must be 655360..8294400")
        ratio = width / height
        if ratio < 1 / 3 or ratio > 3:
            failures.append("aspect ratio must be between 1:3 and 3:1")
        if failures:
            if not allow_extensions:
                raise CliError(f"invalid gpt-image-2 size {size}: {'; '.join(failures)}")
            warnings.append("provider-extension-size-validation-bypassed")
    elif profile and not profile.get("supports_flexible_size", False):
        allowed = {"1024x1024", "1536x1024", "1024x1536"}
        if size not in allowed:
            if not allow_extensions:
                raise CliError(f"{family} accepts auto or one of: {', '.join(sorted(allowed))}")
            warnings.append("provider-extension-size-validation-bypassed")
    return warnings


def validate_output_path(path: Path, output_format: str, force: bool) -> None:
    suffix = path.suffix.lower()
    allowed_suffixes = {".png"} if output_format == "png" else ({".jpg", ".jpeg"} if output_format == "jpeg" else {".webp"})
    if suffix not in allowed_suffixes:
        raise CliError(f"--out extension does not match --output-format {output_format}")
    if path.is_symlink():
        raise CliError(f"refusing symlink output: {path}")
    if path.exists() and not force:
        raise CliError(f"output exists; pass --force to replace: {path}")


def image_format_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "png"
    if suffix in {".jpg", ".jpeg"}:
        return "jpeg"
    if suffix == ".webp":
        return "webp"
    return "unknown"


def validate_input_file(path: Path, *, mask: bool = False) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise CliError(f"input file not found: {path}")
    if path.is_symlink():
        raise CliError(f"refusing symlink input: {path}")
    size = path.stat().st_size
    if size <= 0 or size >= MAX_INPUT_BYTES:
        raise CliError(f"input file must be 1 byte..under 50 MB: {path}")
    data = path.read_bytes()
    image = detect_image(data)
    if image["format"] not in KNOWN_IMAGE_FORMATS:
        raise CliError(f"unsupported input format: {path}")
    if image_format_from_path(path) != image["format"]:
        raise CliError(f"input extension does not match detected format: {path}")
    if mask:
        if image["format"] != "png":
            raise CliError("mask must be PNG")
        if not image.get("alpha", False):
            raise CliError("mask PNG must contain an alpha channel")
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "image": image,
    }


def validate_args(args: argparse.Namespace) -> tuple[str, dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if args.edit:
        args.mode = "edit"
    if not args.mode:
        args.mode = "edit" if args.input_image or args.mask else "generation"
    args.size = resolve_size(args.size)

    if args.list_size_presets or args.list_model_profiles or args.list_remote_models:
        return "", None, warnings
    if bool(args.prompt) == bool(args.prompt_file):
        raise CliError("use exactly one of --prompt or --prompt-file")
    if not args.out:
        raise CliError("--out is required")
    if args.mode == "edit" and not args.input_image:
        raise CliError("edit mode requires --input-image")
    if args.mode == "generation" and (args.input_image or args.mask):
        raise CliError("--input-image and --mask require edit mode")
    if len(args.input_image) > MAX_INPUT_IMAGES:
        raise CliError(f"at most {MAX_INPUT_IMAGES} input images are allowed")
    if not 1 <= args.n <= 10:
        raise CliError("--n must be 1..10")
    if not 0 <= args.partial_images <= 3:
        raise CliError("--partial-images must be 0..3")
    if args.partial_images and not args.stream:
        raise CliError("--partial-images requires --stream")
    if args.output_compression is not None:
        if not 0 <= args.output_compression <= 100:
            raise CliError("--output-compression must be 0..100")
        if args.output_format == "png":
            raise CliError("--output-compression applies only to jpeg or webp")
    if args.background == "transparent" and args.output_format == "jpeg":
        raise CliError("transparent background requires png or webp")
    if args.timeout_seconds < 1:
        raise CliError("--timeout-seconds must be positive")
    if args.max_download_bytes < 1:
        raise CliError("--max-download-bytes must be positive")

    profile, profile_warnings = resolve_model_profile(args.model)
    warnings.extend(profile_warnings)
    if profile is None and args.strict_model_profile:
        raise CliError(f"unknown model profile: {args.model}")
    if profile:
        status = profile.get("status")
        if status == "deprecated" and not args.allow_deprecated_model:
            raise CliError(
                f"{args.model} is deprecated and scheduled to shut down on {profile.get('shutdown')}; "
                f"use {profile.get('replacement')} or pass --allow-deprecated-model"
            )
        if status == "retired" and not args.allow_retired_model:
            raise CliError(
                f"{args.model} retired on {profile.get('shutdown')}; "
                "use gpt-image-2 or explicitly pass --allow-retired-model for a reviewed provider route"
            )
        if args.stream and not profile.get("supports_streaming") and not args.allow_provider_extensions:
            raise CliError(f"{args.model} is not documented for Images API streaming")
        if args.background == "transparent" and not profile.get("supports_transparency"):
            raise CliError(f"{args.model} does not support transparent background")
        if args.input_fidelity and profile.get("input_fidelity") == "always-high":
            raise CliError(f"{args.model} always uses high input fidelity; omit --input-fidelity")
    if args.input_fidelity and args.mode != "edit":
        raise CliError("--input-fidelity requires edit mode")
    if args.response_format and model_is_known_gpt(profile) and not args.allow_provider_extensions:
        raise CliError("official GPT Image responses use b64_json; --response-format requires --allow-provider-extensions")
    if args.param and not args.allow_provider_extensions:
        raise CliError("--param requires --allow-provider-extensions")

    warnings.extend(validate_size(args.size, profile, args.allow_provider_extensions))
    out = Path(args.out).expanduser()
    validate_output_path(out, args.output_format, args.force)
    args.out = str(out)
    return read_prompt(args), profile, warnings


def read_prompt(args: argparse.Namespace) -> str:
    prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8") if args.prompt_file else str(args.prompt)
    if not prompt.strip():
        raise CliError("prompt is empty")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise CliError(f"prompt exceeds {MAX_PROMPT_CHARS} characters")
    return prompt


def endpoint_from_base_url(value: str, mode: str) -> str:
    normalized = value.strip().rstrip("/")
    if not normalized:
        raise CliError("--base-url is required")
    validate_endpoint_url(normalized)
    suffix = "edits" if mode == "edit" else "generations"
    if re.search(r"/v1/images/(?:generations|edits)$", normalized, re.I):
        return re.sub(r"/(?:generations|edits)$", f"/{suffix}", normalized, flags=re.I)
    if re.search(r"/images/(?:generations|edits)$", normalized, re.I):
        return re.sub(r"/(?:generations|edits)$", f"/{suffix}", normalized, flags=re.I)
    if normalized.endswith("/v1"):
        return f"{normalized}/images/{suffix}"
    return f"{normalized}/v1/images/{suffix}"


def models_endpoint(value: str) -> str:
    normalized = value.strip().rstrip("/")
    validate_endpoint_url(normalized)
    if normalized.endswith("/v1"):
        return f"{normalized}/models"
    if re.search(r"/v1/images/(?:generations|edits)$", normalized, re.I):
        return re.sub(r"/images/(?:generations|edits)$", "/models", normalized, flags=re.I)
    return f"{normalized}/v1/models"


def validate_endpoint_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return
    raise CliError("endpoint must use HTTPS, except localhost")


def read_api_key(args: argparse.Namespace) -> str:
    key = first_env("IMAGE_API_KEY", "NEWAPI_API_KEY", "NEW_API_KEY", "OPENAI_API_KEY")
    if key:
        return key.strip()
    if not args.token_file:
        raise CliError("missing API key; set an environment variable or pass --token-file")
    path = Path(args.token_file).expanduser()
    if not path.exists() or not path.is_file():
        raise CliError(f"token file not found: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077 and not args.allow_insecure_token_file:
        raise CliError(f"token file permissions are too broad ({oct(mode)}); use chmod 600 or pass --allow-insecure-token-file")
    key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise CliError("token file is empty")
    return key


def build_payload(args: argparse.Namespace, prompt: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.n,
        "background": args.background,
        "output_format": args.output_format,
        "moderation": args.moderation,
    }
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    if args.input_fidelity:
        payload["input_fidelity"] = args.input_fidelity
    if args.response_format:
        payload["response_format"] = args.response_format
    if args.stream:
        payload["stream"] = True
        payload["partial_images"] = args.partial_images
    for raw in args.param:
        key, value = parse_param(raw)
        payload[key] = value
    return payload


def request_json(url: str, api_key: str, payload: dict[str, Any], timeout: int, stream: bool = False) -> Any:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    return open_request(request, timeout)


def multipart_body(payload: dict[str, Any], images: list[Path], mask: Path | None) -> tuple[bytes, str]:
    boundary = f"----image-api-workbench-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    def field(name: str, value: Any) -> None:
        serialized = json.dumps(value, separators=(",", ":")) if isinstance(value, (dict, list)) else str(value)
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                serialized.encode("utf-8"),
                b"\r\n",
            ]
        )

    def file_field(name: str, path: Path) -> None:
        mime = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}[image_format_from_path(path)]
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            ]
        )

    for key, value in payload.items():
        field(key, value)
    for image in images:
        file_field("image", image)
    if mask:
        file_field("mask", mask)
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def request_multipart(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    images: list[Path],
    mask: Path | None,
    timeout: int,
    stream: bool = False,
) -> Any:
    body, boundary = multipart_body(payload, images, mask)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    request = Request(url, data=body, headers=headers, method="POST")
    return open_request(request, timeout)


def open_request(request: Request, timeout: int) -> Any:
    try:
        return urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise CliError(f"image API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise CliError(f"image API connection failed: {exc.reason}") from exc


def read_json_response(response: BinaryIO) -> dict[str, Any]:
    raw = response.read()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliError(f"API returned non-JSON response: {raw[:500]!r}") from exc
    if not isinstance(value, dict):
        raise CliError("API response must be a JSON object")
    return value


def iter_sse(response: Iterable[bytes]) -> Iterable[dict[str, Any]]:
    event_name = ""
    data_lines: list[str] = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                text = "\n".join(data_lines)
                if text != "[DONE]":
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise CliError(f"invalid SSE JSON payload: {text[:500]}") from exc
                    if isinstance(payload, dict):
                        if event_name and "type" not in payload:
                            payload["type"] = event_name
                        yield payload
            event_name = ""
            data_lines = []
            continue
        if line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        text = "\n".join(data_lines)
        if text != "[DONE]":
            payload = json.loads(text)
            if isinstance(payload, dict):
                if event_name and "type" not in payload:
                    payload["type"] = event_name
                yield payload


def b64_from_item(item: dict[str, Any]) -> str:
    for candidate in (
        item.get("b64_json"),
        (item.get("data") or {}).get("b64_json") if isinstance(item.get("data"), dict) else None,
        (item.get("image") or {}).get("b64_json") if isinstance(item.get("image"), dict) else None,
    ):
        if candidate:
            return str(candidate)
    return ""


def url_from_item(item: dict[str, Any]) -> str:
    for candidate in (
        item.get("url"),
        (item.get("data") or {}).get("url") if isinstance(item.get("data"), dict) else None,
        (item.get("image") or {}).get("url") if isinstance(item.get("image"), dict) else None,
    ):
        if candidate:
            return str(candidate)
    return ""


def ensure_write_path(path: Path, force: bool) -> None:
    if path.is_symlink():
        raise CliError(f"refusing symlink output: {path}")
    if path.exists() and not force:
        raise CliError(f"output exists; pass --force to replace: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def write_image(path: Path, data: bytes, expected_format: str, force: bool) -> dict[str, Any]:
    image = detect_image(data)
    if image["format"] == "unknown":
        raise CliError("image response format is unknown")
    if image["format"] != expected_format:
        raise CliError(f"image response format {image['format']} does not match requested {expected_format}")
    ensure_write_path(path, force)
    path.write_bytes(data)
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "image": image,
    }


def output_path_for_index(out: Path, index: int) -> Path:
    if index == 0:
        return out
    return out.with_name(f"{out.stem}-{index + 1:02d}{out.suffix}")


def partial_path(partial_dir: Path, index: int, output_format: str) -> Path:
    extension = "jpg" if output_format == "jpeg" else output_format
    return partial_dir / f"partial-{index + 1:02d}.{extension}"


def download_image(url: str, timeout: int, max_bytes: int, allow_insecure_localhost: bool) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        localhost = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if not (localhost and allow_insecure_localhost):
            raise CliError("returned image URL must use HTTPS, except explicitly allowed localhost")
    request = Request(url, headers={"Accept": "image/*"})
    response = open_request(request, timeout)
    final = urlparse(response.geturl())
    if final.scheme != "https":
        localhost = final.scheme == "http" and final.hostname in {"127.0.0.1", "localhost", "::1"}
        if not (localhost and allow_insecure_localhost):
            raise CliError("image URL redirected to an insecure destination")
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
    if content_type and not content_type.startswith("image/"):
        raise CliError(f"image URL returned unexpected Content-Type: {content_type}")
    data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise CliError(f"image URL exceeded --max-download-bytes ({max_bytes})")
    return data


def save_nonstream_response(json_value: dict[str, Any], args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    items = json_value.get("data")
    if not isinstance(items, list) or not items:
        raise CliError("image API response missing data[0]")
    if len(items) < args.n:
        raise CliError(f"requested {args.n} images but API returned {len(items)}")
    outputs = []
    response_kind = ""
    for index, item in enumerate(items[: args.n]):
        if not isinstance(item, dict):
            raise CliError(f"image API data[{index}] is not an object")
        encoded = b64_from_item(item)
        url = url_from_item(item)
        if encoded:
            try:
                data = base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise CliError(f"invalid base64 in data[{index}]") from exc
            response_kind = response_kind or "b64_json"
        elif url:
            data = download_image(url, args.timeout_seconds, args.max_download_bytes, args.allow_insecure_localhost)
            response_kind = response_kind or "url"
        else:
            raise CliError(f"image response data[{index}] has neither b64_json nor url")
        outputs.append(
            write_image(output_path_for_index(Path(args.out), index), data, args.output_format, args.force)
        )
    return outputs, response_kind


def save_stream_response(response: Iterable[bytes], args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    partials: list[dict[str, Any]] = []
    completion: dict[str, Any] = {}
    partial_dir = Path(args.partial_dir).expanduser() if args.partial_dir else Path(args.out).parent / f"{Path(args.out).stem}-partials"
    for event in iter_sse(response):
        event_type = str(event.get("type", ""))
        encoded = b64_from_item(event)
        if "partial" in event_type and encoded:
            data = base64.b64decode(encoded, validate=True)
            path = partial_path(partial_dir, len(partials), args.output_format)
            partials.append(write_image(path, data, args.output_format, args.force))
        elif "completed" in event_type:
            completion = event
            if encoded:
                data = base64.b64decode(encoded, validate=True)
                outputs.append(
                    write_image(output_path_for_index(Path(args.out), len(outputs)), data, args.output_format, args.force)
                )
        elif event_type.endswith(".failed") or event.get("error"):
            raise CliError(f"stream failed: {json.dumps(event.get('error') or event, ensure_ascii=False)[:1200]}")
    if not outputs:
        raise CliError("stream completed without a final image")
    return outputs, partials, completion


def detect_image(data: bytes) -> dict[str, Any]:
    if len(data) >= 26 and data[:8] == b"\x89PNG\r\n\x1a\n":
        color_type = data[25]
        return {
            "format": "png",
            "width": struct.unpack(">I", data[16:20])[0],
            "height": struct.unpack(">I", data[20:24])[0],
            "alpha": color_type in {4, 6},
        }
    if len(data) >= 4 and data[:2] == b"\xff\xd8":
        return detect_jpeg(data)
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return detect_webp(data)
    return {"format": "unknown", "width": None, "height": None, "alpha": None}


def detect_jpeg(data: bytes) -> dict[str, Any]:
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        if offset + 4 > len(data):
            break
        length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
        if length < 2:
            break
        if marker in {*range(0xC0, 0xC4), *range(0xC5, 0xC8), *range(0xC9, 0xCC), *range(0xCD, 0xD0)}:
            return {
                "format": "jpeg",
                "width": struct.unpack(">H", data[offset + 7 : offset + 9])[0],
                "height": struct.unpack(">H", data[offset + 5 : offset + 7])[0],
                "alpha": False,
            }
        offset += 2 + length
    return {"format": "jpeg", "width": None, "height": None, "alpha": False}


def detect_webp(data: bytes) -> dict[str, Any]:
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        flags = data[20]
        return {
            "format": "webp",
            "width": 1 + int.from_bytes(data[24:27], "little"),
            "height": 1 + int.from_bytes(data[27:30], "little"),
            "alpha": bool(flags & 0x10),
        }
    return {"format": "webp", "width": None, "height": None, "alpha": None}


def requested_dimensions(size: str) -> tuple[int | None, int | None]:
    match = re.fullmatch(r"(\d+)x(\d+)", size)
    return (int(match.group(1)), int(match.group(2))) if match else (None, None)


def size_match(size: str, image: dict[str, Any]) -> bool | None:
    width, height = requested_dimensions(size)
    if width is None or image.get("width") is None:
        return None
    return width == image.get("width") and height == image.get("height")


def write_metadata(path_value: str | None, out: Path, metadata: dict[str, Any], force: bool) -> str | None:
    if path_value == "none":
        return None
    path = Path(path_value).expanduser() if path_value else Path(f"{out}.meta.json")
    ensure_write_path(path, force)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def list_remote_models(args: argparse.Namespace) -> None:
    api_key = read_api_key(args)
    endpoint = models_endpoint(args.base_url)
    request = Request(endpoint, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    response = open_request(request, args.timeout_seconds)
    payload = read_json_response(response)
    rows = payload.get("data", [])
    ids = sorted({str(item.get("id")) for item in rows if isinstance(item, dict) and item.get("id")})
    candidates = [model for model in ids if re.search(r"image|dall-e|imagen|nano-banana|gemini", model, re.I)]
    print_json(
        {
            "ok": True,
            "endpoint": endpoint,
            "model_count": len(ids),
            "image_model_candidates": candidates,
            "evidence_boundary": "catalog-only; endpoint support requires a real request",
        }
    )


def safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = dict(payload)
    prompt = str(value.get("prompt", ""))
    value["prompt"] = prompt if len(prompt) <= 180 else prompt[:180] + "..."
    return value


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    load_env_defaults()
    parser = build_parser()
    args = parser.parse_args()
    if args.list_size_presets:
        print_json({"ok": True, "presets": SIZE_PRESETS})
        return 0
    if args.list_model_profiles:
        print_json({"ok": True, "profiles": MODEL_PROFILES})
        return 0
    if args.list_remote_models:
        list_remote_models(args)
        return 0

    prompt, profile, warnings = validate_args(args)
    endpoint = endpoint_from_base_url(args.base_url, args.mode)
    payload = build_payload(args, prompt)
    input_paths = [Path(value).expanduser() for value in args.input_image]
    input_metadata = [validate_input_file(path) for path in input_paths]
    mask_path = Path(args.mask).expanduser() if args.mask else None
    mask_metadata = validate_input_file(mask_path, mask=True) if mask_path else None
    if mask_metadata and input_metadata:
        if mask_metadata["image"]["width"] != input_metadata[0]["image"]["width"] or mask_metadata["image"]["height"] != input_metadata[0]["image"]["height"]:
            raise CliError("mask dimensions must match the first input image")

    if args.dry_run:
        print_json(
            {
                "ok": True,
                "dry_run": True,
                "mode": args.mode,
                "endpoint": endpoint,
                "payload": safe_payload(payload),
                "model_profile": profile,
                "warnings": warnings,
                "input_images": input_metadata,
                "mask": mask_metadata,
                "out": args.out,
                "metadata_out": args.metadata_out or f"{args.out}.meta.json",
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            }
        )
        return 0

    api_key = read_api_key(args)
    started = time.monotonic()
    response = (
        request_multipart(endpoint, api_key, payload, input_paths, mask_path, args.timeout_seconds, args.stream)
        if args.mode == "edit"
        else request_json(endpoint, api_key, payload, args.timeout_seconds, args.stream)
    )
    if args.stream:
        outputs, partials, response_meta = save_stream_response(response, args)
        response_kind = "sse-b64_json"
        usage = response_meta.get("usage")
        created = response_meta.get("created")
    else:
        response_meta = read_json_response(response)
        outputs, response_kind = save_nonstream_response(response_meta, args)
        partials = []
        usage = response_meta.get("usage")
        created = response_meta.get("created")

    elapsed_ms = round((time.monotonic() - started) * 1000)
    metadata: dict[str, Any] = {
        "ok": True,
        "skill": "image-api-workbench",
        "skill_version": VERSION,
        "mode": args.mode,
        "endpoint": endpoint,
        "model": args.model,
        "model_profile": profile,
        "requested_size": args.size,
        "quality": args.quality,
        "n": args.n,
        "background": args.background,
        "output_format": args.output_format,
        "output_compression": args.output_compression,
        "moderation": args.moderation,
        "input_fidelity": args.input_fidelity,
        "stream": args.stream,
        "partial_images_requested": args.partial_images,
        "response_kind": response_kind,
        "outputs": outputs,
        "partial_outputs": partials,
        "actual_size_matches_request": [size_match(args.size, item["image"]) for item in outputs],
        "elapsed_ms": elapsed_ms,
        "created": created,
        "usage": usage,
        "input_images": input_metadata,
        "mask": mask_metadata,
        "warnings": warnings,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }
    if args.include_prompt_preview:
        metadata["prompt_preview"] = prompt if len(prompt) <= 240 else prompt[:240] + "..."
    metadata_path = write_metadata(args.metadata_out, Path(args.out), metadata, args.force)
    print_json(
        {
            "ok": True,
            "mode": args.mode,
            "outputs": outputs,
            "partial_outputs": partials,
            "metadata": metadata_path,
            "response_kind": response_kind,
            "elapsed_ms": elapsed_ms,
            "warnings": warnings,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CliError as exc:
        print_json({"ok": False, "error": str(exc)})
        raise SystemExit(2)
    except KeyboardInterrupt:
        print_json({"ok": False, "error": "interrupted"})
        raise SystemExit(130)
