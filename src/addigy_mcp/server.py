import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import AddigyClient
from .api_client_v1 import AddigyV1Client
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets these before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
# This server speaks two unrelated Addigy API generations, each with its own
# auth scheme, so v1 and v2 credentials are tracked independently — a caller
# only needs to send the header set for whichever tools it actually calls.
_v2_creds_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "addigy_v2_creds", default=None
)
_v1_creds_var: contextvars.ContextVar[tuple[str, str, str] | None] = contextvars.ContextVar(
    "addigy_v1_creds", default=None
)


def get_v2_client_from_context(settings: Settings) -> AddigyClient | None:
    """Resolve the active AddigyClient (v2) for the current request context."""
    api_key = _v2_creds_var.get()
    if not api_key:
        return None
    return AddigyClient(api_key, settings.addigy_base_url)


def get_v1_client_from_context() -> AddigyV1Client | None:
    """Resolve the active AddigyV1Client for the current request context."""
    creds = _v1_creds_var.get()
    if not creds:
        return None
    client_id, client_secret, site = creds
    return AddigyV1Client(client_id, client_secret, site)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Addigy-Api-Key (v2) and/or X-Addigy-V1-Client-Id +
    X-Addigy-V1-Client-Secret + X-Addigy-V1-Site (v1, all three required
    together) from request headers and stores them in separate contextvars.
    Returns 401 on /mcp requests only if NEITHER credential set is present —
    a caller that only wants v1 (or only v2) tools need not send the other
    scheme's headers; a v1/v2 tool called without its own credentials
    returns a clear per-tool error instead.
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
        v2_api_key = request.headers.get("x-addigy-api-key")
        v1_client_id = request.headers.get("x-addigy-v1-client-id")
        v1_client_secret = request.headers.get("x-addigy-v1-client-secret")
        v1_site = request.headers.get("x-addigy-v1-site")
        v1_complete = bool(v1_client_id and v1_client_secret and v1_site)

        if not v2_api_key and not v1_complete:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        "This server requires either the X-Addigy-Api-Key header "
                        "(Addigy API v2) or all three of X-Addigy-V1-Client-Id, "
                        "X-Addigy-V1-Client-Secret, X-Addigy-V1-Site (Addigy API v1)"
                    ),
                    "required_headers": [],
                    "optional_headers": [
                        "X-Addigy-Api-Key",
                        "X-Addigy-V1-Client-Id",
                        "X-Addigy-V1-Client-Secret",
                        "X-Addigy-V1-Site",
                    ],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        v2_token = _v2_creds_var.set(v2_api_key)
        v1_token = _v1_creds_var.set(
            (v1_client_id, v1_client_secret, v1_site) if v1_complete else None
        )
        try:
            await self.app(scope, receive, send)
        finally:
            _v2_creds_var.reset(v2_token)
            _v1_creds_var.reset(v1_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Addigy tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="addigy-mcp",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    v2_client_factory: Callable[[], AddigyClient | None] = lambda: get_v2_client_from_context(settings)
    v1_client_factory: Callable[[], AddigyV1Client | None] = lambda: get_v1_client_from_context()

    from .tools import alerts, apps, devices, policies
    from .tools import v1_addigy

    devices.register(mcp, v2_client_factory)
    alerts.register(mcp, v2_client_factory)
    policies.register(mcp, v2_client_factory)
    apps.register(mcp, v2_client_factory)
    v1_addigy.register(mcp, v1_client_factory)

    return mcp
