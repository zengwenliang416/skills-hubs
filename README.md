# skills-hubs

Wenliang Zeng 常用且经过实际验证的 AI Agent Skills 集合。

仓库按 `skills/<skill-name>/` 组织，每个 Skill 都是自包含目录，并保留自己的
安装说明、运行脚本、测试、安全边界和许可证。

## Skills

| Skill                                                                     | 版本  | 用途                                                        | 安装                                                   |
| ------------------------------------------------------------------------- | ----- | ----------------------------------------------------------- | ------------------------------------------------------ |
| [image-api-workbench](skills/image-api-workbench)                         | 2.1.0 | 通过 OpenAI Images API 或兼容网关生成、编辑、探测并验证图片 | `npm install --global image-api-workbench`             |
| [amicro-universal-frontend-style](skills/amicro-universal-frontend-style) | 1.1.0 | 将作用域 Amicro 风格、Token 和安全微交互迁移到现有前端      | `npm install --global amicro-universal-frontend-style` |

## 安装到 Codex

克隆仓库后，将需要的 Skill 复制到 Codex Skills 目录：

```bash
git clone https://github.com/zengwenliang416/skills-hubs.git
mkdir -p ~/.codex/skills
cp -R skills-hubs/skills/image-api-workbench \
  ~/.codex/skills/image-api-workbench
cp -R skills-hubs/skills/amicro-universal-frontend-style \
  ~/.codex/skills/amicro-universal-frontend-style
```

也可以通过 npm 安装 Skill 提供的全局 CLI：

```bash
npm install --global image-api-workbench
image-api-workbench --version

npm install --global amicro-universal-frontend-style
amicro-inspect-frontend --help
amicro-style-layer --help
amicro-verify-style --help
amicro-generate-tokens --help
```

## Web 展示站

`web/` 是仓库的 Amicro 风格展示前端（Vite + React + TypeScript），
在构建期直接读取根目录 `catalog.json` 生成技能目录页，支持搜索、分类筛选、
完整 Skill 详情、安装与文档入口，以及亮/暗/跟随系统三态主题。`server/` 是
Rust + Axum + SQLite 统计服务，按 IP 统计访客和 Skill 行为、代理并缓存 npm
官方下载量，并在生产模式同源托管前端。架构、设计模式与代码规范见
[web/README.md](web/README.md) 和 [server/README.md](server/README.md)。

```bash
cd web
npm install
npm run build
cd ..
cargo run --manifest-path server/Cargo.toml

# 开发模式：先启动上面的 Rust 服务，再在另一个终端运行
cd web
npm run dev        # /api 自动代理到 127.0.0.1:8080
npm run test && npm run typecheck && npm run lint && npm run format:check
```

## 收录原则

- Skill 必须能够独立安装和运行。
- 不提交 API key、token、Cookie、`.env` 或本机私密配置。
- 不提交缓存、生成图片、临时报告或构建产物。
- 每个 Skill 必须声明自己的许可证和安全边界。
- 发布前至少运行该 Skill 自带的测试和安装冒烟检查。

## 版本发布

正式版本统一通过 80 服务器上的 Woodpecker 流水线发布，不从开发机直接执行
`npm publish`。

发布 tag 使用 `<skill-name>@<semver>` 格式，例如：

```bash
git tag -a 'image-api-workbench@2.1.0' \
  -m 'release: image-api-workbench 2.1.0'
git push origin 'image-api-workbench@2.1.0'
```

流水线会校验 tag、`catalog.json` 和 Skill 元数据版本完全一致，重新运行测试，
生成并校验 npm tarball，然后幂等发布 npm 包并创建 GitHub Release。完整流程和
Secret 边界见 [发布指南](docs/RELEASING.md)。

## 许可证

本仓库不使用统一许可证。每个 Skill 的授权范围以其目录中的 `LICENSE`
为准。公开可见不等于获得复制、修改或再分发授权。
