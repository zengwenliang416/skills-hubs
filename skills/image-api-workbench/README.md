# Image API Workbench

`image-api-workbench` is a local Codex skill for reproducible image generation,
reference-image editing, route diagnostics, and artifact verification through
the OpenAI Images API or compatible gateways such as NewAPI.

It replaces `newapi-imagegen`. The new name describes the capability rather
than binding the workflow to one gateway implementation.

## Quick Start

Install the command-line tools from npm:

```bash
npm install --global image-api-workbench
```

Python 3.9 or newer is required at runtime. The CLI itself uses only the Python
standard library.

Dry-run a current GPT Image request:

```bash
image-api-workbench \
  --prompt "A clean editorial AI infrastructure cover, no text, no logos" \
  --size 1536x864 \
  --quality high \
  --out ./artifacts/cover.png \
  --dry-run
```

Inspect the configured gateway catalog without generating an image:

```bash
image-api-workbench --list-remote-models
```

Generate a transparent image:

```bash
image-api-workbench \
  --prompt "A transparent editorial icon of an AI accelerator, no text" \
  --model gpt-image-2 \
  --background transparent \
  --output-format png \
  --out ./artifacts/icon.png
```

Edit a reference image:

```bash
image-api-workbench \
  --input-image ./artifacts/master-zh.png \
  --prompt "Preserve every non-text visual detail and replace only visible Chinese copy with clear English." \
  --size 1536x864 \
  --quality high \
  --out ./artifacts/master-en.png
```

Request streaming partial images from a compatible endpoint:

```bash
image-api-workbench \
  --prompt "A cinematic industrial robot assembly line, no text" \
  --stream \
  --partial-images 2 \
  --partial-dir ./artifacts/partials \
  --out ./artifacts/final.png
```

## Configuration

Secret/config resolution:

1. CLI `--token-file` and `--base-url`;
2. current process environment;
3. `<cwd>/.content-skills/.env`;
4. `~/.content-skills/.env`;
5. `/root/.openclaw/new-api.token` when present.

Supported environment variables:

```text
NEWAPI_API_KEY
NEW_API_KEY
OPENAI_API_KEY
IMAGE_API_KEY
NEWAPI_BASE_URL
OPENAI_BASE_URL
OPENAI_API_BASE
IMAGE_API_BASE_URL
NEWAPI_TOKEN_FILE
IMAGE_API_TOKEN_FILE
IMAGE_API_TIMEOUT_SECONDS
```

Prefer an environment variable or a permission-restricted token file. Do not
put keys in prompts, shell history, skill files, reports, metadata, or memory.

## Main Options

```text
--prompt TEXT
--prompt-file PATH
--out PATH
--mode generation|edit
--input-image PATH              Repeatable, maximum 16
--mask PATH
--model MODEL                   Default: gpt-image-2
--size auto|WIDTHxHEIGHT|preset
--quality auto|low|medium|high
--n 1..10
--background auto|opaque|transparent
--output-format png|jpeg|webp
--output-compression 0..100
--moderation auto|low
--input-fidelity low|high
--stream
--partial-images 0..3
--partial-dir DIR
--metadata-out PATH|none
--include-prompt-preview
--list-model-profiles
--list-size-presets
--list-remote-models
--dry-run
```

Known-model validation is strict by default. Use
`--allow-provider-extensions` only after checking the target gateway's
documentation and exact endpoint behavior.

## Bilingual Review

Create a contact sheet after reference-image localization:

```bash
image-api-bilingual-review \
  --left-dir ./artifacts/zh-CN \
  --right-dir ./artifacts/en \
  --left-label "Chinese master" \
  --right-label "English edit" \
  --title "Localized image review" \
  --out ./artifacts/localized-review.html
```

The contact sheet writes HTML plus a JSON metadata sidecar containing file
hashes, dimensions, byte sizes, and missing-pair status.

## Codex Skill Installation

The npm package includes the complete Skill source. To install it into Codex
instead of using only the global CLI:

```bash
mkdir -p ~/.codex/skills
cp -R "$(npm root --global)/image-api-workbench" \
  ~/.codex/skills/image-api-workbench
```

## Verification

After a real request, check:

```bash
file ./artifacts/cover.png
sed -n '1,260p' ./artifacts/cover.png.meta.json
```

The sidecar records requested and actual dimensions separately. A requested
`3840x2160` image that returns another size is not native 4K and must not be
reported as such.

## Scope Boundary

This package intentionally owns reproducible Images API requests. OpenAI's
Responses API image-generation tool is a separate conversational/multi-turn
surface and is documented in `references/model-support.md`; this CLI does not
pretend that an Images API request is a Responses API workflow.
