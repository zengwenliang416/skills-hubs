# Prototype Question: skill-product-foundation

## Question

`第一阶段是否应采用一条固定、最小且保护隐私的数据流：前端先完成用户动作，再 best-effort 上报四种固定 Skill 事件；Rust 服务依据 catalog allowlist 和可信代理策略校验请求，将 IP 仅存入按 UTC 日聚合的 SQLite 行，并只向前端返回聚合指标？`

## Branch

`data-flow`

## Review Target

- Entry: `data-flow-map.md`
- Required reviewer decision: 确认该数据流、错误语义、保留期与组件边界可作为第一阶段生产实现依据。

## Out of Scope

- Production implementation.
- Database writes.
- Deployment behavior.
