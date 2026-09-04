import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import AddigyClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
_gateway_creds_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "addigy_gateway_creds", default=None
)


def get_client_from_context(settings: Settings) -> AddigyClient | None:
    """Resolve the active AddigyClient for the current request context."""
    api_key = _gateway_creds_var.get()
    if not api_key:
        return None
    return AddigyClient(api_key, settings.addigy_base_url)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Addigy-Api-Key (required) from request headers and stores it in
    the contextvar. Returns 401 if the header is missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        api_key = request.headers.get("x-addigy-api-key")
        if not api_key:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": "This server requires the X-Addigy-Api-Key header",
                    "required_headers": ["X-Addigy-Api-Key"],
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set(api_key)
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Addigy tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="addigy-mcp",
        instructions=(
            "Addigy is a macOS/iOS device management (MDM) platform MSPs use to "
            "manage clients' Apple device fleets — enrollment, policy enforcement, "
            "monitoring, and software inventory. Use this server for: device "
            "inventory/fleet questions (addigy_query_devices), monitoring/compliance "
            "alerts (addigy_get_alerts), policy lookups (addigy_query_policies), and "
            "installed-app inventory split by enrollment method — native agent "
            "(addigy_query_installed_apps_agent) vs MDM-only "
            "(addigy_query_installed_apps_mdm). All 5 tools are read-only queries; "
            "there are no write/delete tools in this service. Typical flow: "
            "addigy_query_policies to find a policy ID, then "
            "addigy_query_devices(policy_id=...) to see which devices are on it."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        stateless_http=True,
        json_response=True,
    )

    client_factory: Callable[[], AddigyClient | None] = lambda: get_client_from_context(settings)

    from .tools import alerts, apps, devices, policies

    devices.register(mcp, client_factory)
    alerts.register(mcp, client_factory)
    policies.register(mcp, client_factory)
    apps.register(mcp, client_factory)

    return mcp
