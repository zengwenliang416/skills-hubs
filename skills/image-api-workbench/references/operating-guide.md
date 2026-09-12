# Operating Guide

## Request Sequence

1. Confirm prompt, output path, and intended aspect ratio.
2. Run `--show-config` and verify the profile, endpoint, model, timeout, and
   field sources.
3. Run `--list-model-profiles` when a model is unfamiliar.
4. Run `--list-remote-models` when gateway availability matters.
5. Run the exact parameter combination with `--dry-run`.
6. Obtain user approval before a paid compatibility probe.
7. Run the real request.
8. Inspect stdout, final image, metadata, and any partial images.

## Reference Editing

Pass one or more `--input-image` values to use `/v1/images/edits`.

For style-preserving localization:

1. approve one visual master;
2. edit the master instead of independently regenerating each language;
3. ask the model to preserve composition, palette, icons, camera angle,
   texture, subjects, and every non-text detail;
4. replace visible copy only;
5. compare the source and localized result in a contact sheet.

Example prompt:

```text
Edit this exact image. Preserve the composition, subjects, icons, colors,
camera angle, texture, and all non-text visual details. Replace only visible
Chinese copy with clear English labels. Do not add scenes, change the visual
system, or simplify the illustration.
```

## Streaming

`--stream` requests SSE from the Images API. `--partial-images` must be `0..3`.
Partial assets are saved under `--partial-dir` or beside the final output.

Compatible gateways may list GPT Image 2.5 models but fail to relay partial
events.
Classify that as a gateway/adapter limitation, not a prompt failure.

## Error Classification

- `401` / `403`: credential or authorization problem.
- `404`: base URL, endpoint, adapter, or model-route mismatch.
- `408` / timeout: network or upstream execution timeout.
- `413`: request or input-image payload is too large.
- `429`: quota, rate limit, or capacity.
- `502` / `503`: gateway or upstream availability.
- `524`: an intermediary gateway stopped waiting for the image upstream before
  the client timeout elapsed. Increasing only `--timeout-seconds` does not
  change the gateway's proxy timeout.
- catalog success plus request failure: endpoint compatibility is unproven.

Do not respond to an availability or authentication error by rewriting the
prompt.

## Metadata Review

Check:

- `model` and `model_profile`;
- `endpoint` and `mode`;
- `requested_size`, detected `image`, and
  `actual_size_matches_request`;
- `response_kind`;
- `input_images` and `mask` lineage;
- `partial_outputs`;
- `warnings`;
- `prompt_sha256`.

Prompt text is omitted by default. Use `--include-prompt-preview` only when the
artifact directory is appropriate for that content.

## Deprecation And Provider Overrides

`--allow-deprecated-model` is a temporary migration escape hatch, not a
recommendation. `--allow-retired-model` is for explicitly reviewed
provider-owned routes only.

`--allow-provider-extensions` permits parameters or dimensions outside the
built-in official model profile. Use it only when the exact gateway
documentation and a real endpoint test justify the exception.
