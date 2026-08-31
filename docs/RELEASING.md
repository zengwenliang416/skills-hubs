# Release Guide

正式版本由 `ci.motion-cover.com` 上的 Woodpecker 和
`production-80` agent 发布。开发机不得直接执行 `npm publish`。

## Required Secrets

Woodpecker 仓库 `zengwenliang416/skills-hubs` 需要两个仓库级 Secret：

- `npm_publish_token`：npm granular access token。只允许发布本仓库中的 npm
  包，设置最短可接受有效期，并启用 bypass 2FA for publishing。
- `github_release_token`：GitHub fine-grained token。只授权
  `zengwenliang416/skills-hubs`，权限限制为 `Contents: Read and write` 与
  `Metadata: Read-only`。

Secret 值只能由仓库所有者在 Woodpecker UI 中录入。不得粘贴到聊天、提交、
日志、命令行参数或仓库文件。

## Prepare a Release

以 `image-api-workbench` 为例：

1. 更新 `skills/image-api-workbench/package.json` 的版本。
2. 同步更新 Skill 的 `manifest.json`、注册元数据和根目录 `catalog.json`。
3. 运行 `python3 scripts/ci/verify_repository.py`。
4. 提交并推送 `main`，等待 Woodpecker `quality` 通过。
5. 创建 annotated tag：

```bash
git tag -a 'image-api-workbench@2.0.1' \
  -m 'release: image-api-workbench 2.0.1'
git push origin 'image-api-workbench@2.0.1'
```

## Pipeline Contract

`quality` 会：

- 检查 Git tracked files 中的凭据和本机绝对路径；
- 校验 `catalog.json` 与每个 Skill 的包元数据；
- 运行每个 Skill 的测试；
- 执行 npm dry-run 并验证文件 allowlist。

`release` 只响应 tag，并会：

- 要求 tag 使用 `<skill-name>@<semver>`；
- 要求 tag commit 位于 `origin/main`；
- 校验 catalog、package、manifest 和 registry 版本一致；
- 重新运行 npm tests，构建 tarball、SHA-256 和 release manifest；
- 如果 npm 版本不存在则发布；如果已存在且 integrity 完全相同则安全跳过；
- 如果已存在但 integrity 不同则停止；
- 拒绝覆盖已有 GitHub Release；
- 上传 tarball、SHA-256 和 release manifest。

## Failure Recovery

- npm 未发布：修复后删除失败 tag，重新提交版本修复，再创建新 tag。
- npm 已发布但 GitHub Release 失败：修复 GitHub 权限后重新运行同一 pipeline。
  npm 步骤只会在 registry integrity 与本次 tarball 完全相同时跳过。
- npm 已存在但 integrity 不同：不得覆盖或 unpublish，必须升级 patch 版本。
- 已存在 GitHub Release：流水线拒绝修改，人工检查后使用新版本修复。
