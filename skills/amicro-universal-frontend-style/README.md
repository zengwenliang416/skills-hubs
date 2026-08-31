# Amicro Universal Frontend Style Skill v1.1.0

一个可复用、跨框架的 Agent Skill，用于把 **Amicro 的视觉语言与微交互语法**迁移到任意前端页面，而不是强制复制上游的 React、Tailwind 或 Motion 技术栈。

## 能力

- 识别 React、Next.js、Vue、Nuxt、Svelte、Astro、Tailwind、CSS Modules、CSS-in-JS 与现有动效工具。
- 将页面、表面、舞台、文字、边框、品牌强调色等角色映射为作用域 Token。
- 提供卡片、按钮、导航、表单、切换、提示、文本/图标交换、光泽和页面转场配方。
- 默认使用目标项目已有技术栈，不自动安装依赖，不联网，不修改 `package.json`。
- 检查键盘焦点、主题、对比度、移动端溢出风险、危险动效和 reduced-motion。

## 安装 Skill

将运行版 ZIP 解压到宿主支持的 Skills 目录。常见项目级位置：

```text
.agents/skills/amicro-universal-frontend-style/
```

显式调用：

```text
$amicro-universal-frontend-style 把 src/pages/pricing.tsx 改成 Amicro 风格，保留现有品牌色、文案、组件 API 和业务逻辑。
```

自然语言能否自动触发取决于宿主的语义路由；显式 `$amicro-universal-frontend-style` 最可靠。

## 检查目标项目

```bash
python3 scripts/inspect_frontend.py /path/to/project --format markdown
```

报告只能写到目标项目内部：

```bash
python3 scripts/inspect_frontend.py /path/to/project \
  --format json \
  --output reports/amicro-inventory.json
```

绝对路径、`../` 逃逸和符号链接逃逸都会被拒绝。

## 安装样式层

默认仅 dry-run：

```bash
python3 scripts/install_style_layer.py /path/to/project \
  --destination src/styles/amicro
```

显式安装：

```bash
python3 scripts/install_style_layer.py /path/to/project \
  --destination src/styles/amicro \
  --apply
```

默认管理：

- `amicro-tokens.css`
- `amicro-primitives.css`
- `amicro-motion.css`
- `amicro-tokens.json`
- `amicro-tokens.ts`
- `.amicro-install.json` 安装清单与文件哈希

需要 TypeScript 动效 helper 时添加 `--include-presets`。

安全更新：

```bash
python3 scripts/install_style_layer.py /path/to/project \
  --destination src/styles/amicro \
  --update --apply
```

卸载：

```bash
python3 scripts/install_style_layer.py /path/to/project \
  --destination src/styles/amicro \
  --uninstall --apply
```

被本地修改的受管文件默认不会被更新或删除；只有显式 `--force` 才会覆盖漂移。

## 导入和作用域

```css
@import "./amicro/amicro-tokens.css";
@import "./amicro/amicro-primitives.css";
@import "./amicro/amicro-motion.css";
```

```html
<main class="amicro" data-amicro-root data-amicro-theme="auto">
  <!-- existing product UI -->
</main>
```

Token 的权威源是 `assets/amicro-tokens.json`。检查生成物一致性：

```bash
python3 scripts/generate_token_assets.py .
```

维护者需要重新生成 CSS/TypeScript 时使用 `--write`。

## 静态验证

```bash
python3 scripts/verify_amicro_style.py /path/to/project --strict
```

写入目标内部报告：

```bash
python3 scripts/verify_amicro_style.py /path/to/project \
  --strict --format json \
  --output reports/amicro-verification.json
```

静态扫描不能证明视觉正确。真实验收至少应覆盖 320、360、768、1440px，明暗主题、键盘、触摸、唯一可访问名称、RTL（适用时）、reduced-motion、控制台错误和横向溢出。

## 源码验证

从源码仓库运行标准库测试：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/generate_token_assets.py .
python3 scripts/verify_amicro_style.py . --strict
```

测试覆盖路径约束、前端探测、Token 生成一致性、静态验证，以及样式层
dry-run/install/update/drift/uninstall 生命周期。npm runtime 包不包含测试与评测
夹具；它们保留在源码仓库中供维护和发布验证。

真实浏览器验收仍需在具体目标项目上完成，不能由静态测试替代。

## 分发边界

- **npm runtime 包**：实际安装使用，不包含测试、评测和生成报告。
- **Git 源码**：包含测试、触发与输出评测，以及维护元数据。
- 宿主适配声明只描述目录与元数据兼容性，不代表所有宿主都完成在线实机认证。

独立人类盲审与生产采用 telemetry 仍是 `missing evidence`，因此不作
“world-class”或生产采用声明。

## 来源与许可

本 Skill 基于 Amicro 公开 MIT 仓库进行框架中立化整理。归属与边界见 `THIRD_PARTY_NOTICES.md` 和 `references/source-notes.md`。
