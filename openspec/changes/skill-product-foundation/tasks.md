## 1. Catalog Product Content

用户结果：访客可以从目录和搜索结果中看到真实、足够决策的 Skill 内容。

- [x] 1.1 Extend the catalog schema and both Skill entries with factual descriptions, tags, highlights, use cases, install methods, and outbound URLs.
- [x] 1.2 Update frontend catalog types and search indexing for the expanded fields.

## 2. Rust Engagement Backend

用户结果：访客的访问和 Skill 行为可以由 Rust 服务安全记录、去重并聚合。

- [x] 2.1 Add catalog Skill allowlist parsing and fixed event request/response models.
- [x] 2.2 Upgrade SQLite to schema v3 with incremental v2 preservation, event upserts, and per-Skill aggregates.
- [x] 2.3 Add `POST /api/events`, expand `/api/metrics`, and cover validation, proxy, migration, and aggregate behavior with tests.

## 3. Skill Detail Product Loop

用户结果：访客可以在同一个详情体验中评估、安装并打开 Skill 资料。

- [x] 3.1 Expand the shared Skill detail with description, tags, highlights, use cases, metadata, install methods, and outbound actions.
- [x] 3.2 Add best-effort event reporting for detail views, successful command copies, documentation clicks, and repository clicks.
- [x] 3.3 Make the expanded dialog responsive, theme-compatible, keyboard/touch accessible, and reduced-motion safe.

## 4. Engagement Metrics

用户结果：访客和维护者可以看到可解释的 Skill 热度与 npm 数据可用性。

- [x] 4.1 Add typed Skill engagement metrics and render a per-Skill behavior panel.
- [x] 4.2 Mark npm totals as partial when any package data is unavailable.

## 5. Documentation And Verification

用户结果：维护者可以依据文档、安全边界和可复现验证结果运行第一阶段产品。

- [x] 5.1 Update root, web, and server documentation for catalog content, event API, schema v3, analytics privacy, and npm partial data.
- [x] 5.2 Run Rust fmt/test/clippy, frontend typecheck/lint/format/build, Amicro strict verification, OpenSpec validation, and end-to-end API checks.
