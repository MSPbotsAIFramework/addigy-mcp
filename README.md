# addigy-mcp

**Addigy V2** MCP server — exposes the Addigy Cyber Platform API (v2) as MCP tools.

> **Naming note:** app.mspbots.ai has two separate Addigy integrations: **"Addigy"** (`subject_code = ADDIGY`, legacy auth via Site + Client ID + Client Secret) and **"Addigy V2"** (`subject_code = ADDIGYV2`, auth via a single API Key). This server implements **Addigy V2** only, matching the ClickUp task's scope.

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## What is Addigy / when would an agent use this

Addigy is a macOS/iOS device management (MDM) platform MSPs use to manage their clients' Apple device fleets — enrollment, policy enforcement, monitoring, and software inventory. An agent should reach for this MCP for requests like:

- "How many Macs does this customer have, and what OS versions are they on?" → `addigy_query_devices`
- "Any monitoring alerts for this org in the last week?" → `addigy_get_alerts`
- "What policies exist / which devices are on policy X?" → `addigy_query_policies`, then `addigy_query_devices` with `policy_id`
- "Is Zoom / a specific app installed across this fleet?" → `addigy_query_installed_apps_agent` (agent-enrolled devices) or `addigy_query_installed_apps_mdm` (MDM-only devices)

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and covers the **5 interfaces** that MSPbots' own Addigy V2 integration actually uses, matching the interface scope configured in MSPbots' `sys_integration`/`sys_integration_api` tables:

| Tool | Addigy API |
|---|---|
| `addigy_query_devices` | `POST /devices` |
| `addigy_get_alerts` | `GET /monitoring/received-alerts` |
| `addigy_query_policies` | `POST /oa/policies/query` |
| `addigy_query_installed_apps_agent` | `POST /oa/installed-apps/agent/query` |
| `addigy_query_installed_apps_mdm` | `POST /oa/installed-apps/mdm/query` |

It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

The underlying Addigy v2 API authenticates via a single static **API Key** (`x-api-key` header), created in the Addigy console under Account → Integrations — matching the single "API Key" field configured in MSPbots' Addigy V2 integration. This server forwards the caller-supplied key as-is; it never stores or persists it.

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

Every request to `/mcp` must include the following HTTP header:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-Addigy-Api-Key` | string | 必填 | 无 | 无(自由文本) | Addigy 静态 API Key,在 Addigy 控制台 Account → Integrations 里创建,本服务将其原样转发为 Addigy 官方 API 要求的 `x-api-key` header,从不落盘存储。 | `X-Addigy-Api-Key: <api_key>` |

Missing the header returns `401 Unauthorized`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |
| `ADDIGY_BASE_URL` | `https://api.addigy.com/api/v2` | Addigy API base URL |

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-Addigy-Api-Key: <api_key>` (required)

## Tool List

**5 tools**, matching the exact interface count MSPbots' own Addigy V2 integration uses.

| Tool | 功能 | 参数 |
|---|---|---|
| `addigy_query_devices` | 按设备属性(fact)条件搜索设备 | `page?`, `per_page?`, `search_any?`, `policy_id?`, `filters?`(列表,每项含 audit_field/operation/type/value/range_value), `desired_fact_identifiers?`, `sort_field?`, `sort_direction?` |
| `addigy_get_alerts` | 查已接收的监控告警列表 | `page`(必填), `per_page`(必填), `status?` |
| `addigy_query_policies` | 查全部策略或按 ID 过滤策略 | `policies?`(策略 ID 列表,省略则返回全部), `multitenancy?`, `child_organizations?` |
| `addigy_query_installed_apps_agent` | 查设备已装应用(Agent 上报,仅 macOS) | `agent_ids`(必填), `sort_field`(必填,"agent_id"/"name"), `sort_direction`(必填,"asc"/"desc"), `names?`, `page?`, `per_page?`, `multitenancy?`, `child_organizations?` |
| `addigy_query_installed_apps_mdm` | 查设备已装应用(MDM 上报) | `agent_ids`(必填), `limit`(必填), `skip`(必填), `sort_direction`(必填), `sort_field`(必填), `multitenancy?`, `child_organizations?` |

`multitenancy`/`child_organizations` apply to the three `/oa/...` endpoints and control whether results include descendant (child) organizations, per Addigy's "Child Organizations" API convention.

## 测试示例 (Test Example)

Query policies:

```json
{
  "method": "tools/call",
  "params": { "name": "addigy_query_policies", "arguments": {} }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

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

A parameterized call:

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

- Documentation: `https://api.addigy.com/api/v2/documentation/`
- Auth: single `x-api-key` header (API keys created under Addigy Account → Integrations)

## Known Gaps / Implementation Notes

- Scope is intentionally limited to the 5 interfaces MSPbots' Addigy V2 integration is configured to use, not the full Addigy API surface (which spans 300+ endpoints across devices, MDM commands, policies, benchmarks, scripts, webhooks, and many third-party integration passthroughs).
- `page`/`per_page` on `addigy_get_alerts` are typed as strings because the vendor's own OpenAPI spec defines them as `type: string` (despite being numeric page/size values) — passed through as-is.
- Not yet tested against a live Addigy account — only protocol-level verification (health check, 401 on missing header, `tools/list` returning all 5 tools) has been done so far.
