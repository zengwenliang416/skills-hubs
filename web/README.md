# Skills Hub Web

仓库根目录 `catalog.json` 的展示前端：Amicro 风格的单页 "Skills Hub" 站点，
展示技能目录、支持搜索与分类筛选、呈现真实访客、Skill 行为与 npm 下载统计，
并以完整详情对话框提供能力、场景、安装、快速开始、文档和源码入口。

## 技术栈

- Vite + React 18 + TypeScript（strict）
- 无 UI 组件库 / CSS 框架 / 路由库；运行时依赖为 `react`、`react-dom` 与 `motion`
  （`motion/react`，framer-motion 官方继任包，供移植的 Amicro 组件使用）
- CSS Modules，无路由库的单页应用（视图用状态切换）

## 目录结构

```
web/
├── index.html              # <html lang="zh-CN" data-amicro-root>，内联预置主题脚本
├── vite.config.ts          # alias: "@catalog" -> ../catalog.json；"@" -> /src
└── src/
    ├── styles/
    │   ├── amicro-tokens.css   # 唯一 token 来源，从技能 assets 原样复制，禁止手改
    │   ├── hub-tokens.css      # 语义角色别名层：--hub-* 仅映射到 --amicro-*，不引入新色值
    │   └── base.css            # 重置、页面骨架、skip link、focus-visible、reduced-motion 兜底
    ├── lib/
    │   ├── theme.tsx           # ThemeProvider + useTheme：light/dark/auto
    │   ├── clipboard.ts        # copyTextToClipboard：Clipboard API + execCommand 回退
    │   ├── springs.ts          # spring 预设（card/tilt/magnetic，移植自 @subhanhq/amicro，MIT）
    │   ├── useScrollProgress.ts / useFinePointerMotion.ts
    │   └── useMediaQuery.ts / useInView.ts / useAmbientActive.ts
    ├── components/             # 自有 primitives：Button / IconButton / Chip / StageCard / CountUp /
    │   │                       #   CopyButton / CodeBlock / EmptyState
    │   └── amicro/             # 移植组件：TextReveal / FadeUp / FadeIn / TiltCard /
    │                           #   MagneticButton / CardCarousel（文件头有出处注释）
    ├── features/catalog/       # 目录、schema 校验、完整详情（Skill Object Hub）、精选任务浏览与行为事件客户端
    ├── features/metrics/       # Rust API 客户端、访客/npm/Skill 行为统计面板
    ├── features/palette/       # ⌘K/Ctrl+K 命令面板：动作命令 + 技能搜索、分组、键盘导航、直达详情
    └── sections/               # 页面区块：Header / Hero / HowItWorks / Contribute / Footer
```

## 设计模式

- **Token 作用域**：所有设计值来自 `amicro-tokens.css`，通过
  `:where(.amicro, [data-amicro-scope], [data-amicro-root])` 作用域生效；`<html>` 挂
  `data-amicro-root`（与 `data-amicro-theme` 同元素，token 文件的 auto 暗色媒体查询规则要求两者同挂）。
  组件样式一律引用 `var(--amicro-*)`；语义角色（action/success/warning/danger/info）经
  `hub-tokens.css` 的 `--hub-*` 别名引用，禁止硬编码色值。
- **catalog 契约**：`features/catalog/schema.ts` 的 `validateCatalog()` 对构建期导入的
  `catalog.json` 做运行时校验（必填字段、数组形状、重名拒绝），`safeExternalUrl()` 仅放行
  http/https 外链；`skillLinks()` 返回已消毒链接，缺失或不安全时 UI 显示「未声明」。
- **主题三态**：`ThemeProvider` 将 `light` / `dark` / `auto` 写入根元素
  `data-amicro-theme` 并持久化到 `localStorage`（默认 `auto`）；`auto` 的解析由 token
  文件内置的 `prefers-color-scheme` 规则完成。`index.html` 内联脚本在首帧前应用持久化主题，避免闪烁。
- **动效纪律**：所有非必要动画/过渡只声明在
  `@media (prefers-reduced-motion: no-preference)` 内；`base.css` 在
  `reduce` 下提供全局即时切换兜底。hover 效果用 `@media (hover: hover)` 门控。
- **有目的的动效**（purposeful motion）：通用动效组件移植自 Amicro registry
  （`components/amicro/`）：Hero 标题 `TextReveal`（按行 clip reveal，整行动画不拆字）、
  区块与网格 `FadeUp`/`FadeIn`（whileInView once 语义）；网格卡片外包 `TiltCard`
  （3D 视差倾斜）；Header 主题按钮与 Footer CTA 外包 `MagneticButton`；"精选浏览"区使用
  `CardCarousel` 扇形卡片架（任意数量可跑，prev/next 端点禁用、点状指示器
  aria-current、侧卡点击前移）。统计 count-up（`CountUp`）进入视口触发一次；
  卡片 stage 的循环氛围动画（media 流光 / frontend-design 色板脉冲，只动
  transform/opacity）通过 `data-ambient` + `useAmbientActive` 在离屏、隐藏标签页或
  dialog 打开时暂停；hover 时 stage 内一次性 sheen 扫过；dialog 先播出场动画再真正
  close（焦点归还不受影响）；主题图标以 key 重挂载实现 rotate/fade swap；Header 顶部有
  滚动进度条（`useScrollProgress`，状态指示，reduced-motion 下保留）。
- **签名交互**：主题切换在支持 View Transitions API 且未启用 reduced motion 时，从主题
  按钮圆心扩散揭示新主题，并按视口角点动态计算覆盖半径；Header 搜索按钮或 `⌘K/Ctrl+K`
  打开命令面板，支持名称、标题和分类搜索、方向键选择及 Enter 直达详情；stage 卡片在精细
  指针环境下显示 transform 驱动的低亮度追光；详情对话框提供安装命令复制、成功/失败文字
  与图标双通道反馈。
- **指针动效降级**：`TiltCard` / `MagneticButton` 仅在
  `(hover: hover) and (pointer: fine)` 且 `prefers-reduced-motion: no-preference`
  时启用（`useFinePointerMotion`，matchMedia 判定）；否则渲染静态元素、不挂
  mousemove 监听。reduced-motion 下 `TextReveal`/`FadeUp`/`FadeIn` 直接呈现终态，
  carousel 过渡时长置 0 但控件全部可用。
- **可访问性**：skip link 直达 `#main`；键盘 focus 有独立可见 ring（`--amicro-focus`）；
  icon button 强制 `aria-label`；触控目标 ≥ 40px；状态不只依赖颜色（chip 文字 + 圆点）；
  详情与命令面板使用原生 `<dialog>`（Esc、背板点击关闭、焦点归还）；命令面板分组展示
  动作与技能结果并以 live region 播报结果数；轮播支持方向键/Home/End。
- **整卡单目标**：`SkillCard` 用 stretched-button 模式（标题按钮的 `::after` 覆盖整卡），
  一张卡只有一个交互目标，不嵌套交互控件。
- **数据来源**：构建期直接 import 仓库根目录的 `catalog.json`（`@catalog` alias）。
  每个 Skill 条目同时提供简介、标签、亮点、场景、安装方法、快速开始和资源链接；
  分类、搜索与详情均由其派生。运行数据通过同源 `POST /api/visits`、
  `POST /api/events` 与 `GET /api/metrics` 获取：前端不生成访客标识，Rust 服务保存
  客户端 IP 并按 UTC 日期聚合；固定记录详情查看、成功复制安装命令、文档点击和
  源码点击。事件上报是 best-effort，失败不会阻止用户操作。npm 周下载量来自官方
  downloads API，单包失败显示缓存或“暂无数据”，汇总会标记为部分数据。

## 代码规范

- CSS Modules，类名 camelCase；一个文件只导出一个组件（样式文件除外）。
- 界面文案用简体中文；代码注释与标识符用英文。
- 组件受控、props 显式类型；保持简单，不滥用 `forwardRef`。
- ESLint flat config：typescript-eslint recommended + react-hooks + jsx-a11y + prettier 收尾。

## 命令

```bash
npm install        # 安装依赖
npm run dev        # 开发服务器；/api 代理到 127.0.0.1:8080
npm run test       # Vitest 聚焦行为测试
npm run build      # 生产构建（dist/）
npm run preview    # 仅静态预览，不包含统计 API
npm run typecheck  # tsc --noEmit
npm run lint       # eslint .
npm run format     # prettier --write .
npm run format:check
```

## Credits

- 通用动效组件（`src/components/amicro/`：TextReveal、FadeUp、FadeIn、TiltCard、
  MagneticButton、CardCarousel）与 `src/lib/springs.ts`、`src/lib/useScrollProgress.ts`
  移植自 [Subhan-code/Amicro--Micro-transitions-](https://github.com/Subhan-code/Amicro--Micro-transitions-)
  （npm 包 `@subhanhq/amicro`，MIT 许可证）。移植时将 Tailwind 类翻译为本项目的
  CSS Modules + `--amicro-*` token，并补充了 reduced-motion 与指针能力降级；
  各移植文件头部均保留出处注释。
- 运行数据区的信息架构参考同一仓库的 `VisitorsChartCard`、`UserMetrics` 与
  `OverviewChart`，但已移除其 Tailwind、Lucide、Recharts 和静态示例数据，改为
  项目自有 CSS Modules、Amicro token 与真实 Rust API。
