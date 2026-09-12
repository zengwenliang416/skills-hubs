# Model And API Support

Evidence checked on 2026-09-09. Recheck official documentation and the exact
gateway before future model or parameter changes.

## Current Recommendation

Use `gpt-image-2.5-sunburst` for the most capable new Images API generation
and precise editing. Use `gpt-image-2.5-flare` when fast, high-quality
generation and throughput are the priority.

- Most capable model: `gpt-image-2.5-sunburst`
- Faster generation model: `gpt-image-2.5-flare`
- Supported endpoints: `/v1/images/generations`, `/v1/images/edits`
- Output formats: PNG, JPEG, WebP
- Transparent output: PNG or WebP
- Streaming: image generation partial/completed SSE events, with `0..3`
  partial images
- Maximum outputs per request: `10`
- Prompt limit: `32000` characters

For GPT Image 2.5, the detailed Images guide documents:

- width and height from `512` to `3840`;
- both dimensions must be multiples of `16`;
- total pixels from `655360` to `8294400`;
- width:height ratio between `1:3` and `3:1`.

The CLI applies the same documented `3840` edge limit to both GPT Image 2.5
models and `gpt-image-2`.

## Lifecycle

| Model | Status | Action |
| --- | --- | --- |
| `gpt-image-2.5-sunburst` | Current | Default for new work and precise edits |
| `gpt-image-2.5-flare` | Current | Prefer for fast, high-quality generation |
| `gpt-image-2` | Older supported model | Keep only for an explicit route requirement |
| `gpt-image-1.5` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2.5-sunburst` |
| `chatgpt-image-latest` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2.5-sunburst` |
| `gpt-image-1` | Deprecated; shutdown 2026-10-23 | Migrate to `gpt-image-2.5-sunburst` |
| `gpt-image-1-mini` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2.5-sunburst` |
| `dall-e-2`, `dall-e-3` | Shut down 2026-05-12 | Do not use for new requests |

## Parameter Notes

- `background`: `auto`, `opaque`, or `transparent`.
- Transparency requires PNG or WebP; JPEG has no alpha channel.
- `output_compression` applies only to JPEG and WebP.
- `quality`: both GPT Image 2.5 models accept `auto`, `low`, `medium`, `high`,
  `xhigh`, and `max`.
- `moderation`: `auto` or `low`.
- GPT Image responses return base64 image data. Official GPT Image requests do
  not support the legacy `response_format=url` behavior.
- `gpt-image-2` automatically uses high input fidelity; the API does not expose
  an `input_fidelity` choice for it.
- GPT Image 2.5 edits may explicitly request `low` or `high` input fidelity.
- Editing accepts up to 16 PNG, JPEG, or WebP inputs under 50 MB each.
- A mask must be a PNG with an alpha channel and match the first input image's
  dimensions.

## API Surface Boundary

The Images API is best for a reproducible, single request that produces or
edits an asset. The Responses API image-generation tool is better for
conversational and multi-turn image workflows. In Responses, a tool-capable
text model is the main response model and `image_generation` is added as a
tool; the image model is selected inside the tool configuration rather than
used as the Responses main model.

## Compatible Gateways

A NewAPI or other OpenAI-compatible `/v1/models` response proves only that the
gateway catalogs a model. It does not prove:

- the model works on both generation and edit endpoints;
- streaming is relayed correctly;
- every official parameter is supported;
- requested dimensions will be returned exactly;
- the channel has quota or current upstream capacity.

Use `--list-remote-models` for catalog evidence, `--dry-run` for local request
validation, and a user-approved paid request for endpoint usability.

## Sources

- OpenAI image generation guide:
  https://developers.openai.com/api/docs/guides/image-generation
- OpenAI Responses image-generation tool:
  https://developers.openai.com/api/docs/guides/tools-image-generation
- GPT Image 2 model page:
  https://developers.openai.com/api/docs/models/gpt-image-2
- GPT Image 2.5 Sunburst model page:
  https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst
- GPT Image 2.5 Flare model page:
  https://developers.openai.com/api/docs/models/gpt-image-2.5-flare
- GPT Image 2.5 launch announcement:
  https://openai.com/index/introducing-gpt-image-2-5/
- OpenAI deprecations:
  https://developers.openai.com/api/docs/deprecations
- OpenAI Images API generate reference:
  https://developers.openai.com/api/reference/resources/images/methods/generate
- OpenAI Images API edit reference:
  https://developers.openai.com/api/reference/resources/images/methods/edit
- NewAPI image generation:
  https://docs.newapi.pro/en/api/openai-image/generate-image
- NewAPI image editing:
  https://docs.newapi.pro/en/api/openai-image/edit-image

NewAPI documentation is useful for route shape, but its model tables can lag
upstream changes. Treat deployment version, channel adapter, model catalog, and
exact endpoint behavior as separate evidence.
