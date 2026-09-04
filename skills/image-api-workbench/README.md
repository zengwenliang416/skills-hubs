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

Create a named gateway profile:

```bash
image-api-workbench \
  --profile pftrader \
  --base-url https://gateway.example.com/v1 \
  --model gpt-image-2 \
  --timeout-seconds 1200 \
  --configure
```

The default profile file is `~/.config/image-api-workbench/config.json`. It is
written atomically with `0600` permissions and may contain only `base_url`,
`model`, `timeout_seconds`, and a `token_file` path. API keys are rejected.

Inspect the final effective configuration before diagnosing a gateway:

```bash
image-api-workbench --profile pftrader --show-config
```

The output reports the selected profile, generation/edit/models endpoints,
credential availability, and the source of every field without exposing key
contents.

Configuration precedence:

1. explicit CLI options;
2. current process environment;
3. selected profile;
4. `<cwd>/.content-skills/.env`;
5. `~/.content-skills/.env`;
6. built-in defaults, including `/root/.openclaw/new-api.token` when present.

Supported environment variables:

```text
IMAGE_API_CONFIG_FILE
IMAGE_API_PROFILE
IMAGE_API_MODEL
IMAGE_API_KEY
IMAGE_API_BASE_URL
IMAGE_API_TOKEN_FILE
IMAGE_API_TIMEOUT_SECONDS
```

Only the `IMAGE_API_*` names above are supported. Unknown or older provider-
specific environment variables are ignored.

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
--config-file PATH
--profile NAME
--configure
--show-config
--list-model-profiles
--list-size-presets
--list-remote-models
--dry-run
```

Known-model validation is strict by default. Use
`--allow-provider-extensions` only after checking the target gateway's
documentation and exact endpoint behavior.

## HTTP 524 Diagnosis

`524` is distinct from the CLI's own socket timeout. It means an intermediary
gateway stopped waiting for the image upstream, often before
`--timeout-seconds` is reached. The CLI reports `error_type`,
`client_timeout_seconds`, `elapsed_ms`, safe response headers, and recommended
actions. Check `--show-config`, gateway image-channel health, upstream latency,
and the gateway proxy timeout before retrying. Do not replay a broad image job
until confirming that the previous upstream job did not finish.

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
