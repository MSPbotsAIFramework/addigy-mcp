# addigy-mcp

**Addigy** MCP server — exposes both Addigy API generations (v2 and the legacy v1) as MCP tools.

> **Naming note:** app.mspbots.ai has two separate Addigy integrations: **"Addigy"** (`subject_code = ADDIGY`, legacy v1 API, auth via Site + Client ID + Client Secret) and **"Addigy V2"** (`subject_code = ADDIGYV2`, v2 API, auth via a single API Key). This single server implements **both**, since they are the same vendor product and MSPbots' own integrations still use both API generations.

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and covers the interfaces that MSPbots' own Addigy integrations actually use, matching the interface scope configured in MSPbots' `sys_integration`/`sys_integration_api` tables:

| Tool | Addigy API |
|---|---|
| **Addigy V2** | |
| `addigy_query_devices` | `POST /devices` |
| `addigy_get_alerts` | `GET /monitoring/received-alerts` |
| `addigy_query_policies` | `POST /oa/policies/query` |
| `addigy_query_installed_apps_agent` | `POST /oa/installed-apps/agent/query` |
| `addigy_query_installed_apps_mdm` | `POST /oa/installed-apps/mdm/query` |
| **Addigy v1 (legacy)** | |
| `addigy_v1_get_devices` | `GET /api/devices` |
| `addigy_v1_get_alerts` | `GET /api/alerts` |
| `addigy_v1_get_applications` | `GET /api/applications` |
| `addigy_v1_get_maintenance` | `GET /api/maintenance` |
| `addigy_v1_get_policies` | `GET /api/policies` |
| `addigy_v1_get_public_software` | `GET /api/catalog/public` |

It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

- **Addigy API v2** authenticates via a single static **API Key** (`x-api-key` header), created in the Addigy console under Account → Integrations — matching the single "API Key" field configured in MSPbots' Addigy V2 integration.
- **Addigy API v1** (legacy, superseded by v2 but still in use for capabilities not yet in v2) authenticates via **`client_id` + `client_secret`** query parameters against a per-organization **Site** domain — matching the Site/Client ID/Client Secret fields configured in MSPbots' legacy Addigy integration.

This server forwards caller-supplied credentials as-is for whichever API generation a tool call targets; it never stores or persists them. A caller only needs to send the header set for the API version it actually calls — v1 and v2 credentials are independent.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m addigy_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok", "service": "addigy-mcp", "transport": "http"}
```

No credentials are required for the health endpoint.

## 授权参数说明 (Authentication)

Every request to `/mcp` must include **either** the v2 header **or** all three v1 headers (a caller wanting both API generations sends all four):

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-Addigy-Api-Key` | string | 二选一(与下方三个 v1 header 组二选一,也可都传) | 无 | 无(自由文本) | **Addigy API v2** 静态 API Key,在 Addigy 控制台 Account → Integrations 里创建,本服务将其原样转发为 Addigy 官方 API 要求的 `x-api-key` header。只调用 v2 工具时需要。 | `X-Addigy-Api-Key: <api_key>` |
| `X-Addigy-V1-Client-Id` | string | 二选一(与 `X-Addigy-Api-Key` 二选一;若提供必须与另外两个 v1 header 一起提供) | 无 | 无(自由文本) | **Addigy API v1**(旧版)的 Client ID,对应 MSPbots "Addigy"(非 V2)集成配置里的 Client Id 字段。只调用 v1 工具时需要。 | `X-Addigy-V1-Client-Id: <client_id>` |
| `X-Addigy-V1-Client-Secret` | string | 同上 | 无 | 无(自由文本) | **Addigy API v1** 的 Client Secret,对应 MSPbots "Addigy"(非 V2)集成配置里的 Client Secret 字段。 | `X-Addigy-V1-Client-Secret: <client_secret>` |
| `X-Addigy-V1-Site` | string | 同上 | 无 | 无(不同组织对应不同域名) | **Addigy API v1** 的组织专属 Site 域名,对应 MSPbots "Addigy"(非 V2)集成配置里的 Site 字段。 | `X-Addigy-V1-Site: prod.addigy.com` |

Missing both the v2 header and a complete v1 header set returns `401 Unauthorized`. Calling a v1 tool with only v2 credentials (or vice versa) returns a clear per-tool error rather than a blanket 401, so a caller using only one API generation doesn't need to send the other's headers at all.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |
| `ADDIGY_BASE_URL` | `https://api.addigy.com` | Addigy API v2 base URL (v1 has no fixed base URL — see `X-Addigy-V1-Site`) |

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-Addigy-Api-Key: <api_key>` and/or `X-Addigy-V1-Client-Id` + `X-Addigy-V1-Client-Secret` + `X-Addigy-V1-Site`

## Tool List

**11 tools total** (5 v2 + 6 v1), matching the exact combined interface count MSPbots' "Addigy" and "Addigy V2" integrations use.

### Addigy V2 (5)

| Tool | 功能 | 参数 |
|---|---|---|
| `addigy_query_devices` | 按设备属性(fact)条件搜索设备 | `page?`, `per_page?`, `search_any?`, `policy_id?`, `filters?`(列表,每项含 audit_field/operation/type/value/range_value), `desired_fact_identifiers?`, `sort_field?`, `sort_direction?` |
| `addigy_get_alerts` | 查已接收的监控告警列表 | `page`(必填), `per_page`(必填), `status?` |
| `addigy_query_policies` | 查全部策略或按 ID 过滤策略 | `policies?`(策略 ID 列表,省略则返回全部), `multitenancy?`, `child_organizations?` |
| `addigy_query_installed_apps_agent` | 查设备已装应用(Agent 上报,仅 macOS) | `agent_ids`(必填), `sort_field`(必填,"agent_id"/"name"), `sort_direction`(必填,"asc"/"desc"), `names?`, `page?`, `per_page?`, `multitenancy?`, `child_organizations?` |
| `addigy_query_installed_apps_mdm` | 查设备已装应用(MDM 上报) | `agent_ids`(必填), `limit`(必填), `skip`(必填), `sort_direction`(必填), `sort_field`(必填), `multitenancy?`, `child_organizations?` |

`multitenancy`/`child_organizations` apply to the three `/oa/...` endpoints and control whether results include descendant (child) organizations, per Addigy's "Child Organizations" API convention.

### Addigy v1 — legacy (6)

| Tool | 功能 | 参数 |
|---|---|---|
| `addigy_v1_get_devices` | 查设备列表 | `page?`(默认 1), `per_page?`(默认 100) |
| `addigy_v1_get_alerts` | 查告警列表 | `page?`(默认 1), `per_page?`(默认 100) |
| `addigy_v1_get_applications` | 查全组织已装应用列表 | `page?`(默认 1), `per_page?`(默认 100) |
| `addigy_v1_get_maintenance` | 查维护项列表 | `page?`(默认 1), `per_page?`(默认 100) |
| `addigy_v1_get_policies` | 查策略列表 | 无 |
| `addigy_v1_get_public_software` | 查公共软件目录 | `page?`(默认 1), `per_page?`(默认 100) |

## 测试示例 (Test Example)

v2 — Query policies:

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-Addigy-Api-Key: <api_key>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "addigy_query_policies", "arguments": {} }
  }'
```

v1 — List devices:

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-Addigy-V1-Client-Id: <client_id>" \
  -H "X-Addigy-V1-Client-Secret: <client_secret>" \
  -H "X-Addigy-V1-Site: prod.addigy.com" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "addigy_v1_get_devices", "arguments": { "page": 1, "per_page": 50 } }
  }'
```

A parameterized v2 call:

```json
{
  "method": "tools/call",
  "params": {
    "name": "addigy_get_alerts",
    "arguments": { "page": "1", "per_page": "50" }
  }
}
```

## API Reference

- v2 documentation: `https://api.addigy.com/api/v2/documentation/` — auth via `x-api-key` header
- v1 documentation: `https://documenter.getpostman.com/view/6033495/S17tPnJf` — auth via `client_id`/`client_secret` query parameters against a per-organization Site domain (the currently published Postman doc only shows a subset of v1 endpoints; the 6 v1 tools here are grounded in MSPbots' own `sys_integration_api` records of method/path/params for the legacy "Addigy" integration)

## Known Gaps / Implementation Notes

- Scope is intentionally limited to the interfaces MSPbots' "Addigy" and "Addigy V2" integrations are configured to use (5 + 6 = 11), not the full Addigy v2 API surface (which spans 300+ endpoints across MDM commands, policies, benchmarks, scripts, webhooks, and many third-party integration passthroughs).
- `page`/`per_page` on `addigy_get_alerts` (v2) are typed as strings because the vendor's own OpenAPI spec defines them as `type: string` (despite being numeric page/size values) — passed through as-is.
- v1 credentials (`client_id`/`client_secret`) are sent as query-string parameters, matching the pattern shown in Addigy's own v1 Postman examples (e.g. "Get Public Software", "Get Specific Custom Software") — Addigy's v1 API is inconsistent about this across endpoints (some examples use headers instead), so this should be verified against a live v1 account on first use.
- Not yet tested against a live Addigy account (either API generation) — only protocol-level verification (health check, 401 when neither credential set is present, correct per-tool error when only one credential set is present, `tools/list` returning all 11 tools) has been done so far.
