# skills-hubs

Wenliang Zeng 常用且经过实际验证的 AI Agent Skills 集合。

仓库按 `skills/<skill-name>/` 组织，每个 Skill 都是自包含目录，并保留自己的
安装说明、运行脚本、测试、安全边界和许可证。

## Skills

| Skill | 版本 | 用途 | 安装 |
| --- | --- | --- | --- |
| [image-api-workbench](skills/image-api-workbench) | 2.0.0 | 通过 OpenAI Images API 或兼容网关生成、编辑、探测并验证图片 | `npm install --global image-api-workbench` |

## 安装到 Codex

克隆仓库后，将需要的 Skill 复制到 Codex Skills 目录：

```bash
git clone https://github.com/zengwenliang416/skills-hubs.git
mkdir -p ~/.codex/skills
cp -R skills-hubs/skills/image-api-workbench \
  ~/.codex/skills/image-api-workbench
```

也可以只安装 `image-api-workbench` 的全局 CLI：

```bash
npm install --global image-api-workbench
image-api-workbench --version
```

## 收录原则

- Skill 必须能够独立安装和运行。
- 不提交 API key、token、Cookie、`.env` 或本机私密配置。
- 不提交缓存、生成图片、临时报告或构建产物。
- 每个 Skill 必须声明自己的许可证和安全边界。
- 发布前至少运行该 Skill 自带的测试和安装冒烟检查。

## 许可证

本仓库不使用统一许可证。每个 Skill 的授权范围以其目录中的 `LICENSE`
为准。公开可见不等于获得复制、修改或再分发授权。
