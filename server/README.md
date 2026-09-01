# Skills Hub Metrics Server

基于 Axum、Tokio 和 SQLite 的最小统计服务，同时从同一 origin 托管前端构建产物。

## 本地启动

先构建前端，再从仓库根目录启动服务：

```bash
cd web
npm run build
cd ..
cargo run --manifest-path server/Cargo.toml
```

默认监听 `127.0.0.1:8080`，静态目录为仓库根目录下的 `web/dist`。

## 环境变量

| 变量                                | 默认值                    | 说明                                       |
| ----------------------------------- | ------------------------- | ------------------------------------------ |
| `SKILLS_HUB_BIND`                   | `127.0.0.1:8080`          | HTTP 监听地址                              |
| `SKILLS_HUB_CATALOG_PATH`           | `catalog.json`            | 技能 catalog 路径                          |
| `SKILLS_HUB_DB_PATH`                | `data/skills-hub.sqlite3` | SQLite 数据库路径                          |
| `SKILLS_HUB_STATIC_DIR`             | `web/dist`                | 前端静态文件目录                           |
| `SKILLS_HUB_TRUSTED_PROXIES`        | 空                        | 可信反向代理 CIDR，逗号分隔                |
| `SKILLS_HUB_WRITE_LIMIT_PER_MINUTE` | `120`                     | 每个解析后客户端 IP 每分钟统计写入上限     |
| `SKILLS_HUB_DB_CONCURRENCY`         | `16`                      | 允许同时进入 SQLite 阻塞任务的最大请求数   |
| `SKILLS_HUB_IP_RETENTION_DAYS`      | `90`                      | 原始 IP 访问和行为聚合数据的保留自然日数量 |

相对路径以服务进程的当前工作目录为基准。生产环境建议显式设置这些变量。

## API

### `POST /api/visits`

无请求体。服务端从 TCP 连接获取客户端 IP，成功后记录一次 page view，并直接
返回与 `GET /api/metrics` 相同的完整指标响应。同一个 IP 在同一个 UTC 日期内
只增加一次 visitor，但每次请求都会增加一次 page view。

默认可信代理列表为空，服务忽略客户端提供的 `Forwarded`、`X-Forwarded-For`
和 `X-Real-IP`，防止伪造 IP。只有当服务部署在明确的可信反向代理之后，才应配置
代理的 CIDR：

```bash
SKILLS_HUB_TRUSTED_PROXIES=127.0.0.1/32,10.0.0.0/8 \
  cargo run --manifest-path server/Cargo.toml
```

只有 TCP 对端命中 allowlist 时才读取转发头。服务优先解析 `Forwarded`，其次
`X-Forwarded-For`，并从右向左移除可信代理 hop，避免直接客户端或追加式代理链
伪造最左侧地址；链缺失时再尝试 `X-Real-IP`，最终回退到 TCP 对端地址。

### `POST /api/events`

请求：

```json
{
  "skill_name": "image-api-workbench",
  "event_type": "install_copy"
}
```

只接受以下固定事件：

- `skill_view`
- `install_copy`
- `documentation_click`
- `repository_click`

`skill_name` 必须存在于启动时加载的 catalog；未知字段和非法值会被拒绝。成功返回
`204 No Content`。事件写入与访问写入共享每 IP 限流和 DB 并发保护，容量不足时返回
`429 Too Many Requests`。

限流器最多保留 4096 个活动键，按固定间隔清理过期窗口，不会在每次请求时扫描全表。
IPv4 按完整地址限流；原生 IPv6 按 `/64` 前缀限流，避免客户端通过快速轮换接口标识
绕过容量保护。SQLite 仍保存完整的解析后 IP，用于同一 UTC 日期内的访客去重。

### `GET /api/metrics`

响应：

```json
{
  "total_visitors": 12,
  "today_visitors": 3,
  "total_page_views": 28,
  "daily_visitors": [
    {
      "date": "2026-08-25",
      "visitors": 0
    }
  ],
  "npm_downloads": [
    {
      "package_name": "image-api-workbench",
      "downloads": 1234,
      "period_start": "2026-08-24",
      "period_end": "2026-08-30",
      "stale": false,
      "error": null
    }
  ],
  "skill_engagement": [
    {
      "skill_name": "image-api-workbench",
      "unique_visitors": 4,
      "views": 8,
      "install_copies": 2,
      "documentation_clicks": 3,
      "repository_clicks": 1
    }
  ]
}
```

`daily_visitors` 始终包含截至当前 UTC 日期的最近 7 天，并为无访问日期补零。
`npm_downloads` 按 catalog 中非空 `npm` 字段的顺序返回，重复包名只保留第一项。
`skill_engagement` 按 catalog Skill 顺序返回，无行为的 Skill 也会得到全零聚合项。
响应不会包含原始 IP。
当前 catalog 包含 `image-api-workbench` 和
`amicro-universal-frontend-style`。若 catalog 不存在、JSON 无效或没有任何 npm
包，服务会在启动阶段失败并给出明确错误。

### `GET /api/healthz`

健康时返回 `200 OK`：

```json
{
  "status": "ok",
  "retention": {
    "healthy": true,
    "last_success_at": "2026-09-01T03:20:00+00:00",
    "last_failure_at": null
  }
}
```

周期 IP 清理失败时返回 `503 Service Unavailable`，`status` 为 `degraded`，
并记录失败时间。详细错误只写入服务 stderr，不通过 API 暴露数据库路径或内部错误。

## npm 降级

npm 下载量来自官方 downloads point API，并缓存 15 分钟。单个包请求失败或返回
404 时不会导致整个指标接口失败：

- 有旧缓存时返回旧值，设置 `stale: true`，并填写 `error`。
- 完全没有缓存时返回 `downloads: null`、空 period、`stale: true` 和 `error`。

失败状态会负缓存 2 分钟，并通过按 package 独立的进程内 singleflight 合并同包
并发刷新。不同 package 可以并行请求，持续 404 或上游故障不会被每个指标请求放大。

## SQLite 与隐私

SQLite 保存 UTC 日期、规范化后的原始 IPv4/IPv6 地址，以及该 IP 当天的 page
view 和固定 Skill 行为次数。IP 地址可能属于个人信息，部署方需要按适用的隐私政策
和法规披露用途、控制数据库访问和备份。数据库文件在 Unix 上设置为 `0600`，服务
默认保留 90 个自然日，并在启动及每 24 小时清理过期访问与行为聚合；可通过
`SKILLS_HUB_IP_RETENTION_DAYS` 调整。服务不安装额外的访问日志中间件。
数据库默认写入 `data/skills-hub.sqlite3`，该目录及 SQLite sidecar 文件已被
Git 忽略。

SQLite 启用 `secure_delete`。清理事务提交后执行 WAL truncate checkpoint，降低
已删除 IP 在当前数据库空闲页和 WAL 中继续残留的概率。该机制不会擦除部署方已经
生成的数据库备份、文件系统快照、磁盘镜像或复制到其他位置的旧文件；这些副本必须
使用同一保留策略单独轮换和删除。`/api/healthz` 只证明当前进程最近一次逻辑清理
是否成功，不证明所有外部备份都已完成物理擦除。

数据库 schema version `3` 新增 `daily_skill_events`。从 schema `2` 升级时保留
现有 IP 访客统计；从旧 UUID schema 升级时仍会重建 `daily_visits` 并清空无法映射
到 IP 的旧数据。旧版二进制不能打开新版数据库，生产升级前应备份 SQLite。

前端资源通过 Axum 从 `SKILLS_HUB_STATIC_DIR` 同源托管；未匹配到静态文件时回退到
`index.html`，支持前端路由刷新。
