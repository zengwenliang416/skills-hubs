# Model And API Support

Evidence checked on 2026-08-30. Recheck official documentation and the exact
gateway before future model or parameter changes.

## Current Recommendation

Use `gpt-image-2` for new Images API generation and editing.

- Stable alias: `gpt-image-2`
- Current documented snapshot: `gpt-image-2-2026-04-21`
- Supported endpoints: `/v1/images/generations`, `/v1/images/edits`
- Output formats: PNG, JPEG, WebP
- Transparent output: PNG or WebP
- Streaming: image generation partial/completed SSE events, with `0..3`
  partial images
- Maximum outputs per request: `10`
- Prompt limit: `32000` characters

For `gpt-image-2`, the detailed Images guide documents:

- width and height from `512` to `4096`;
- both dimensions must be multiples of `16`;
- total pixels from `655360` to `8294400`;
- width:height ratio between `1:3` and `3:1`.

The model page separately lists maximum image width and height as `3840`.
Because those official surfaces are not perfectly aligned, the CLI uses the
more conservative `3840` edge limit by default. A reviewed compatible gateway
may be allowed through `--allow-provider-extensions`.

## Lifecycle

| Model | Status | Action |
| --- | --- | --- |
| `gpt-image-2` | Current | Default for new work |
| `gpt-image-1.5` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2` |
| `chatgpt-image-latest` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2` |
| `gpt-image-1` | Older supported model | Use only for an explicit route requirement |
| `gpt-image-1-mini` | Deprecated; shutdown 2026-12-01 | Migrate to `gpt-image-2` |
| `dall-e-2`, `dall-e-3` | Shut down 2026-05-12 | Do not use for new requests |

## Parameter Notes

- `background`: `auto`, `opaque`, or `transparent`.
- Transparency requires PNG or WebP; JPEG has no alpha channel.
- `output_compression` applies only to JPEG and WebP.
- `quality`: `auto`, `low`, `medium`, or `high`.
- `moderation`: `auto` or `low`.
- GPT Image responses return base64 image data. Official GPT Image requests do
  not support the legacy `response_format=url` behavior.
- `gpt-image-2` automatically uses high input fidelity; the API does not expose
  an `input_fidelity` choice for it.
- Editing accepts up to 16 PNG, JPEG, or WebP inputs under 50 MB each.
- A mask must be a PNG with an alpha channel and match the first input image's
  dimensions.

## API Surface Boundary

The Images API is best for a reproducible, single request that produces or
edits an asset. The Responses API image-generation tool is better for
conversational and multi-turn image workflows. In Responses, a tool-capable
text model is the main response model and `image_generation` is added as a
tool; `gpt-image-2` is selected inside the tool configuration rather than used
as the Responses main model.

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
