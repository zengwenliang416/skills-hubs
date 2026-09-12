#!/usr/bin/env python3

from __future__ import annotations

import base64
import json
import os
import stat
import struct
import subprocess
import tempfile
import threading
import unittest
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/image_api_workbench.py"
CONTACT_SHEET = ROOT / "scripts/bilingual_contact_sheet.py"


def png_bytes(width: int = 1, height: int = 1, alpha: bool = True) -> bytes:
    color_type = 6 if alpha else 2
    pixel = b"\x00\x32\x64\x96\xff" if alpha else b"\x00\x32\x64\x96"
    raw = pixel * height

    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class ApiHandler(BaseHTTPRequestHandler):
    png = png_bytes()
    requests: list[dict] = []

    def log_message(self, _format: str, *_args) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "data": [
                            {"id": "gpt-image-2.5-flare"},
                            {"id": "gpt-image-2.5-sunburst"},
                            {"id": "gpt-image-2"},
                            {"id": "text-model"},
                        ]
                    }
                ).encode()
            )
            return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.requests.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type", ""),
                "body": body,
            }
        )
        if self.path == "/v1/images/generations" and b'"prompt": "force 524"' in body:
            self.send_response(524)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Server", "test-gateway")
            self.send_header("CF-Ray", "test-ray")
            self.end_headers()
            self.wfile.write(b"upstream image timeout")
            return
        if self.path == "/v1/images/generations" and b'"stream": true' in body:
            encoded = base64.b64encode(self.png).decode()
            events = [
                {"type": "image_generation.partial_image", "b64_json": encoded, "partial_image_index": 0},
                {"type": "image_generation.completed", "b64_json": encoded, "usage": {"total_tokens": 7}},
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for event in events:
                self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
            return
        if self.path in {"/v1/images/generations", "/v1/images/edits"}:
            encoded = base64.b64encode(self.png).decode()
            count = 2 if b'"n": 2' in body else 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"created": 1, "data": [{"b64_json": encoded} for _ in range(count)]}).encode()
            )
            return
        self.send_error(404)


class Server:
    def __enter__(self) -> str:
        ApiHandler.requests.clear()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_port}/v1"

    def __exit__(self, *_args) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def run_cli(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    for name in (
        "IMAGE_API_BASE_URL",
        "IMAGE_API_CONFIG_FILE",
        "IMAGE_API_KEY",
        "IMAGE_API_MODEL",
        "IMAGE_API_PROFILE",
        "IMAGE_API_TIMEOUT_SECONDS",
        "IMAGE_API_TOKEN_FILE",
    ):
        merged.pop(name, None)
    merged.update(env or {})
    return subprocess.run(
        ["python3", str(CLI), *args],
        text=True,
        capture_output=True,
        env=merged,
        timeout=30,
        check=False,
    )


class ImageApiWorkbenchTests(unittest.TestCase):
    def test_configure_profile_writes_secure_secret_free_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            result = run_cli(
                [
                    "--config-file",
                    str(config),
                    "--profile",
                    "slow-gateway",
                    "--base-url",
                    "https://images.example.com/v1",
                    "--model",
                    "gpt-image-2",
                    "--timeout-seconds",
                    "180",
                    "--token-file",
                    "/secure/image-api.token",
                    "--configure",
                ],
                env={"IMAGE_API_KEY": "must-not-be-persisted"},
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(config.read_text())
            self.assertEqual(payload["default_profile"], "slow-gateway")
            self.assertEqual(payload["profiles"]["slow-gateway"]["timeout_seconds"], 180)
            self.assertNotIn("api_key", config.read_text().lower())
            self.assertNotIn("must-not-be-persisted", config.read_text())
            self.assertEqual(stat.S_IMODE(config.stat().st_mode), 0o600)

    def test_show_config_reports_sources_without_exposing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "default_profile": "profile-a",
                        "profiles": {
                            "profile-a": {
                                "base_url": "https://profile.example.com/v1",
                                "model": "profile-model",
                                "timeout_seconds": 90,
                            }
                        },
                    }
                )
            )
            result = run_cli(
                ["--config-file", str(config), "--base-url", "https://cli.example.com/v1", "--show-config"],
                env={
                    "IMAGE_API_KEY": "show-config-secret",
                    "IMAGE_API_MODEL": "env-model",
                },
            )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["values"]["base_url"], "https://cli.example.com/v1")
        self.assertEqual(payload["values"]["model"], "env-model")
        self.assertEqual(payload["values"]["timeout_seconds"], 90)
        self.assertEqual(payload["sources"]["base_url"], "cli:--base-url")
        self.assertTrue(payload["sources"]["model"].startswith("env:IMAGE_API_MODEL@"))
        self.assertIn("#profiles.profile-a.timeout_seconds", payload["sources"]["timeout_seconds"])
        self.assertNotIn("show-config-secret", result.stdout)

    def test_profile_overrides_dotenv_but_process_env_overrides_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            dotenv_dir = home / ".content-skills"
            dotenv_dir.mkdir(parents=True)
            (dotenv_dir / ".env").write_text(
                'IMAGE_API_BASE_URL="https://dotenv.example.com/v1"\n'
                "IMAGE_API_MODEL=dotenv-model\n"
            )
            config = Path(tmp) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "default_profile": "profile-a",
                        "profiles": {
                            "profile-a": {
                                "base_url": "https://profile.example.com/v1",
                                "model": "profile-model",
                                "timeout_seconds": 90,
                            }
                        },
                    }
                )
            )
            profile_result = run_cli(
                ["--config-file", str(config), "--show-config"],
                env={"HOME": str(home)},
            )
            process_result = run_cli(
                ["--config-file", str(config), "--show-config"],
                env={
                    "HOME": str(home),
                    "IMAGE_API_BASE_URL": "https://process.example.com/v1",
                },
            )
        self.assertEqual(profile_result.returncode, 0, profile_result.stdout)
        profile_payload = json.loads(profile_result.stdout)
        self.assertEqual(profile_payload["values"]["base_url"], "https://profile.example.com/v1")
        self.assertEqual(profile_payload["values"]["model"], "profile-model")
        self.assertIn("#profiles.profile-a.base_url", profile_payload["sources"]["base_url"])
        self.assertEqual(process_result.returncode, 0, process_result.stdout)
        process_payload = json.loads(process_result.stdout)
        self.assertEqual(process_payload["values"]["base_url"], "https://process.example.com/v1")
        self.assertTrue(process_payload["sources"]["base_url"].startswith("env:IMAGE_API_BASE_URL@"))

    def test_config_rejects_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile_config = Path(tmp) / "profile-config.json"
            profile_config.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {
                            "unsafe": {
                                "base_url": "https://images.example.com/v1",
                                "api_key": "do-not-store-this",
                            }
                        },
                    }
                )
            )
            root_config = Path(tmp) / "root-config.json"
            root_config.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {},
                        "api_key": "also-do-not-store-this",
                    }
                )
            )
            profile_result = run_cli(
                ["--config-file", str(profile_config), "--profile", "unsafe", "--show-config"]
            )
            root_result = run_cli(["--config-file", str(root_config), "--show-config"])
        for result in (profile_result, root_result):
            self.assertEqual(result.returncode, 2)
            self.assertIn("API keys must remain", result.stdout)
            self.assertNotIn("do-not-store-this", result.stdout)

    def test_http_524_is_classified_as_gateway_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, Server() as base_url:
            result = run_cli(
                [
                    "--base-url",
                    base_url,
                    "--prompt",
                    "force 524",
                    "--out",
                    str(Path(tmp) / "timeout.png"),
                    "--timeout-seconds",
                    "30",
                ],
                env={"IMAGE_API_KEY": "test-key"},
            )
        self.assertEqual(result.returncode, 2, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["http_status"], 524)
        self.assertEqual(payload["error_type"], "gateway_or_upstream_timeout")
        self.assertEqual(payload["client_timeout_seconds"], 30)
        self.assertIn("intermediary gateway", payload["diagnosis"])
        self.assertEqual(payload["response_headers"]["cf-ray"], "test-ray")

    def test_default_model_is_sunburst_and_allows_transparency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli(
                [
                    "--config-file",
                    str(Path(tmp) / "missing-config.json"),
                    "--prompt",
                    "transparent test",
                    "--out",
                    str(Path(tmp) / "transparent.png"),
                    "--background",
                    "transparent",
                    "--dry-run",
                ]
            )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["payload"]["model"], "gpt-image-2.5-sunburst")

    def test_deprecated_model_requires_explicit_override(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "deprecated test",
                "--model",
                "gpt-image-1.5",
                "--out",
                "/tmp/image-api-workbench-deprecated.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("2026-12-01", result.stdout)

    def test_deprecated_mini_model_requires_explicit_override(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "deprecated mini test",
                "--model",
                "gpt-image-1-mini",
                "--out",
                "/tmp/image-api-workbench-deprecated-mini.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("2026-12-01", result.stdout)

    def test_gpt_image_1_deprecation_is_enforced(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "deprecated model test",
                "--model",
                "gpt-image-1",
                "--out",
                "/tmp/image-api-workbench-gpt-image-1.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("2026-10-23", result.stdout)

    def test_invalid_gpt_image_2_size_is_rejected(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "size test",
                "--size",
                "3822x1638",
                "--out",
                "/tmp/image-api-workbench-size.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("multiples of 16", result.stdout)

    def test_valid_ultrawide_preset_is_accepted(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "size test",
                "--size",
                "ultrawide",
                "--out",
                "/tmp/image-api-workbench-ultrawide.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["payload"]["size"], "3840x1648")

    def test_sunburst_accepts_4k_and_xhigh_quality(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "quality test",
                "--model",
                "gpt-image-2.5-sunburst",
                "--size",
                "3840x2160",
                "--quality",
                "xhigh",
                "--out",
                "/tmp/image-api-workbench-sunburst.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["payload"]["quality"], "xhigh")

    def test_flare_accepts_max_and_xhigh_quality(self) -> None:
        max_result = run_cli(
            [
                "--prompt",
                "quality test",
                "--model",
                "gpt-image-2.5-flare",
                "--quality",
                "max",
                "--out",
                "/tmp/image-api-workbench-flare-max.png",
                "--dry-run",
            ]
        )
        xhigh_result = run_cli(
            [
                "--prompt",
                "quality test",
                "--model",
                "gpt-image-2.5-flare",
                "--quality",
                "xhigh",
                "--out",
                "/tmp/image-api-workbench-flare-xhigh.png",
                "--dry-run",
            ]
        )
        self.assertEqual(max_result.returncode, 0, max_result.stdout)
        self.assertEqual(xhigh_result.returncode, 0, xhigh_result.stdout)

    def test_2_5_rejects_edge_above_3840(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "size test",
                "--model",
                "gpt-image-2.5-sunburst",
                "--size",
                "4096x1920",
                "--out",
                "/tmp/image-api-workbench-oversize.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("512..3840", result.stdout)

    def test_2_5_snapshot_prefix_uses_flare_profile(self) -> None:
        result = run_cli(
            [
                "--prompt",
                "snapshot test",
                "--model",
                "gpt-image-2.5-flare-2026-09-08",
                "--quality",
                "max",
                "--out",
                "/tmp/image-api-workbench-flare-snapshot.png",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        profile = json.loads(result.stdout)["model_profile"]
        self.assertEqual(profile["family"], "gpt-image-2.5-flare")
        self.assertEqual(profile["snapshot"], "gpt-image-2.5-flare-2026-09-08")

    def test_gpt_image_2_input_fidelity_flag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            source.write_bytes(png_bytes())
            result = run_cli(
                [
                    "--input-image",
                    str(source),
                    "--prompt",
                    "edit",
                    "--model",
                    "gpt-image-2",
                    "--input-fidelity",
                    "high",
                    "--out",
                    str(Path(tmp) / "out.png"),
                    "--dry-run",
                ]
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("always uses high input fidelity", result.stdout)

    def test_sunburst_edit_accepts_high_input_fidelity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            source.write_bytes(png_bytes())
            result = run_cli(
                [
                    "--input-image",
                    str(source),
                    "--prompt",
                    "edit",
                    "--model",
                    "gpt-image-2.5-sunburst",
                    "--input-fidelity",
                    "high",
                    "--out",
                    str(Path(tmp) / "out.png"),
                    "--dry-run",
                ]
            )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["payload"]["input_fidelity"], "high")

    def test_remote_model_catalog_is_catalog_only(self) -> None:
        with Server() as base_url:
            result = run_cli(
                ["--base-url", base_url, "--list-remote-models"],
                env={"IMAGE_API_KEY": "test-key"},
            )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["image_model_candidates"],
            ["gpt-image-2", "gpt-image-2.5-flare", "gpt-image-2.5-sunburst"],
        )
        self.assertIn("catalog-only", payload["evidence_boundary"])

    def test_nonstream_saves_every_requested_output_without_prompt_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, Server() as base_url:
            out = Path(tmp) / "result.png"
            result = run_cli(
                [
                    "--base-url",
                    base_url,
                    "--prompt",
                    "two outputs",
                    "--n",
                    "2",
                    "--out",
                    str(out),
                ],
                env={"IMAGE_API_KEY": "test-key"},
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(out.exists())
            self.assertTrue((Path(tmp) / "result-02.png").exists())
            metadata = json.loads(Path(f"{out}.meta.json").read_text())
            self.assertEqual(len(metadata["outputs"]), 2)
            self.assertNotIn("prompt_preview", metadata)

    def test_stream_saves_partial_and_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, Server() as base_url:
            out = Path(tmp) / "final.png"
            partial_dir = Path(tmp) / "partials"
            result = run_cli(
                [
                    "--base-url",
                    base_url,
                    "--prompt",
                    "stream test",
                    "--stream",
                    "--partial-images",
                    "1",
                    "--partial-dir",
                    str(partial_dir),
                    "--out",
                    str(out),
                ],
                env={"IMAGE_API_KEY": "test-key"},
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(out.exists())
            self.assertTrue((partial_dir / "partial-01.png").exists())

    def test_edit_multipart_includes_input_and_mask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, Server() as base_url:
            source = Path(tmp) / "source.png"
            mask = Path(tmp) / "mask.png"
            source.write_bytes(png_bytes())
            mask.write_bytes(png_bytes())
            out = Path(tmp) / "edit.png"
            result = run_cli(
                [
                    "--base-url",
                    base_url,
                    "--input-image",
                    str(source),
                    "--mask",
                    str(mask),
                    "--prompt",
                    "edit test",
                    "--out",
                    str(out),
                ],
                env={"IMAGE_API_KEY": "test-key"},
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            request = ApiHandler.requests[-1]
            self.assertEqual(request["path"], "/v1/images/edits")
            self.assertIn("multipart/form-data", request["content_type"])
            self.assertIn(b'name="image"', request["body"])
            self.assertIn(b'name="mask"', request["body"])

    def test_contact_sheet_writes_hash_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "left"
            right = Path(tmp) / "right"
            left.mkdir()
            right.mkdir()
            (left / "slide-01.png").write_bytes(png_bytes())
            (right / "slide-01.png").write_bytes(png_bytes())
            out = Path(tmp) / "review.html"
            result = subprocess.run(
                [
                    "python3",
                    str(CONTACT_SHEET),
                    "--left-dir",
                    str(left),
                    "--right-dir",
                    str(right),
                    "--out",
                    str(out),
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            metadata = json.loads(Path(f"{out}.meta.json").read_text())
            self.assertEqual(metadata["count"], 1)
            self.assertEqual(len(metadata["rows"][0]["left"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
