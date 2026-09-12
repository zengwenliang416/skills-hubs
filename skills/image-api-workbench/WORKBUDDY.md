# WorkBuddy Installation

This directory is a standard Agent Skill package. WorkBuddy should load the
skill from the directory that contains `SKILL.md`.

## Install From A Folder Or ZIP

If the WorkBuddy build has an **Import local Skill** or **Import ZIP** action,
select this directory or the provided ZIP archive and restart WorkBuddy.

For manual installation, extract the folder and copy the whole
`image-api-workbench` directory to:

- macOS/Linux: `~/.workbuddy/skills/image-api-workbench`
- Windows: `%USERPROFILE%\.workbuddy\skills\image-api-workbench`

Do not copy only `SKILL.md`; the `scripts/` and `references/` directories are
required for the CLI workflow.

## Runtime Requirements

- Python 3.9 or newer must be available as `python3` (or `python` on Windows).
- WorkBuddy must be allowed to run local shell/Python commands when a request
  needs the bundled CLI.
- The API endpoint must expose OpenAI-compatible
  `/v1/images/generations`, `/v1/images/edits`, and optionally `/v1/models`.

## Configure The Recipient's Own API Route

Use the recipient's own endpoint and API key. Do not send or reuse another
person's key.

macOS/Linux:

```bash
export IMAGE_API_BASE_URL="https://your-gateway.example.com/v1"
export IMAGE_API_KEY="paste-your-own-key-in-the-shell-only"
python3 ~/.workbuddy/skills/image-api-workbench/scripts/image_api_workbench.py \
  --show-config
```

For the current shared gateway, use this URL:

```bash
export IMAGE_API_BASE_URL="https://new-api.motion-cover.com/v1"
```

To avoid putting the key in shell history, enter it silently:

```bash
read -r -s "IMAGE_API_KEY?请输入 API Key（输入不回显）: "
printf '\n'
export IMAGE_API_KEY
```

Persist the endpoint and model profile (the key remains only in the current
shell):

```bash
python3 ~/.workbuddy/skills/image-api-workbench/scripts/image_api_workbench.py \
  --base-url "$IMAGE_API_BASE_URL" \
  --model gpt-image-2 \
  --timeout-seconds 1200 \
  --configure
```

If WorkBuddy is launched outside this terminal, use a permission-restricted
token file instead:

```bash
mkdir -p "$HOME/.config/image-api-workbench"
umask 077
read -r -s "IMAGE_API_KEY?请输入 API Key（输入不回显）: "
printf '\n'
printf '%s\n' "$IMAGE_API_KEY" > "$HOME/.config/image-api-workbench/api.token"
unset IMAGE_API_KEY
chmod 600 "$HOME/.config/image-api-workbench/api.token"

python3 ~/.workbuddy/skills/image-api-workbench/scripts/image_api_workbench.py \
  --base-url "https://new-api.motion-cover.com/v1" \
  --model gpt-image-2 \
  --token-file "$HOME/.config/image-api-workbench/api.token" \
  --timeout-seconds 1200 \
  --configure
```

Windows PowerShell:

```powershell
$env:IMAGE_API_BASE_URL = "https://your-gateway.example.com/v1"
$env:IMAGE_API_KEY = "paste-your-own-key-in-this-session-only"
python "$HOME\.workbuddy\skills\image-api-workbench\scripts\image_api_workbench.py" `
  --show-config
```

The key is intentionally not stored in this package. Prefer the recipient's
secret manager or a permission-restricted token file for persistent use.

## First Use

Ask WorkBuddy:

> 使用 image-api-workbench，用我的 API 配置先做一次 dry-run，不要发起付费请求。

Then, after checking the printed route and model:

```bash
python3 ~/.workbuddy/skills/image-api-workbench/scripts/image_api_workbench.py \
  --prompt "A clean editorial AI infrastructure cover, no text, no logos" \
  --model gpt-image-2 \
  --size 1536x864 \
  --quality high \
  --out ./artifacts/cover.png \
  --dry-run
```

For a real request, remove `--dry-run` only after confirming the endpoint,
quota, and billing scope. A model listed by `/v1/models` is catalog evidence
only; it does not prove that generation or editing works on that gateway.

## Troubleshooting

- If WorkBuddy cannot find the skill, verify that the final path contains
  `SKILL.md` directly and restart WorkBuddy.
- If WorkBuddy cannot execute the workflow, verify Python and local shell
  permission, then run the CLI command manually from the skill directory.
- If the gateway does not list `gpt-image-2`, stop before a paid request.
