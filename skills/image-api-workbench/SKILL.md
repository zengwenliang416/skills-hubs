---
name: image-api-workbench
description: Generate, edit, probe, and verify images through the OpenAI Images API or compatible gateways such as NewAPI. Use for GPT Image generation, reference-image editing, transparent PNG/WebP assets, bilingual visual localization, model catalog checks, streaming partial images, API compatibility tests, covers, social graphics, and publishing assets. Triggers on image API, GPT Image, NewAPI image, gpt-image-2, generate image, edit reference image, 生成图片, 生图, 配图, 封面图, 透明图, 图片编辑, 参考图编辑, 双语图片, 模型可用性. Excludes image search, visual critique, local-only bitmap editing, and requests that explicitly require the built-in image generation tool instead of an API workflow.
---

# Image API Workbench

## Purpose

Run reproducible Images API generation or editing against OpenAI or a reviewed
compatible gateway. The CLI manages named gateway profiles and validates
requests, catalogs, streaming partials, outputs, and evidence. Default to
`gpt-image-2`; catalogs are route evidence, not endpoint proof.

## Workflow

1. Read [model support](references/model-support.md) when changing models or
   advanced parameters.
2. Use `--show-config` for gateway diagnosis. Configure a named profile only
   when a route needs to be persisted; never put an API key in profile JSON.
3. Use `--dry-run` for new or uncertain parameter combinations, and
   `--list-remote-models` only when catalog discovery is needed.
4. Generate with `/v1/images/generations`; add `--input-image` to switch to
   `/v1/images/edits`. Use transparent PNG/WebP or streaming flags when the
   selected endpoint supports them.
5. Save assets outside this skill and inspect the image plus metadata sidecar.

## Safety Defaults

- Deprecated or retired models require an explicit allow flag; keep the current
  model status in [model support](references/model-support.md).
- Retired DALL-E models are blocked unless `--allow-retired-model` is explicit.
- Known GPT Image parameters are model-validated. Provider extensions require
  `--allow-provider-extensions`.
- Credentials come from environment variables or token files. Never persist
  keys in prompts, metadata, skill files, reports, or logs.
- Profile files persist only endpoint, model, timeout, and token-file path.
  They are written with `0600` permissions.
- HTTP `524` means an intermediary gateway stopped waiting for its upstream;
  increasing only the CLI timeout does not extend that gateway's own limit.
- Metadata stores a prompt hash by default. Prompt preview is opt-in.

## Editing And Localization

For matched bilingual visuals, create one approved master and edit that exact
image for each language. Preserve composition and non-text details; replace
visible copy only. Build a side-by-side review with
`scripts/bilingual_contact_sheet.py`.

See [operating guide](references/operating-guide.md) for commands, error
classification, streaming behavior, and verification.
Routing boundaries are covered by `evals/trigger_cases.json`.

## Output Contract

A successful paid call requires:

- stdout JSON has `ok: true`;
- final image exists and is non-empty;
- metadata sidecar exists unless explicitly disabled;
- detected format and dimensions are plausible;
- `actual_size_matches_request` is checked rather than inferred;
- edit metadata identifies each input by path, bytes, SHA-256, and dimensions.

Catalogs and dry runs do not prove endpoint support. Paid probes require user
approval.
