import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client_v1 import AddigyV1Client, AddigyV1Error
from ._common import NO_TOKEN_V1


def register(mcp: FastMCP, client_factory: Callable[[], AddigyV1Client | None]) -> None:
    """Register legacy Addigy API v1 tools.

    Addigy API v2 supersedes v1, but MSPbots' existing "Addigy" (non-V2)
    integration still relies on these 6 read-only v1 endpoints, so this MCP
    server supports both API generations side by side.
    """

    @mcp.tool()
    async def addigy_v1_get_devices(page: int = 1, per_page: int = 100) -> str:
        """List devices in the organization (Addigy API v1).

        API: GET /api/devices

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 100).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get("/api/devices", params={"page": page, "per_page": per_page})
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_v1_get_alerts(page: int = 1, per_page: int = 100) -> str:
        """List alerts in the organization (Addigy API v1).

        API: GET /api/alerts

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 100).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get("/api/alerts", params={"page": page, "per_page": per_page})
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_v1_get_applications(page: int = 1, per_page: int = 100) -> str:
        """List installed applications across the organization's devices (Addigy API v1).

        API: GET /api/applications

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 100).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get(
                "/api/applications", params={"page": page, "per_page": per_page}
            )
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_v1_get_maintenance(page: int = 1, per_page: int = 100) -> str:
        """List maintenance items configured in the organization (Addigy API v1).

        API: GET /api/maintenance

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 100).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get(
                "/api/maintenance", params={"page": page, "per_page": per_page}
            )
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_v1_get_policies() -> str:
        """List policies configured in the organization (Addigy API v1).

        API: GET /api/policies
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get("/api/policies")
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_v1_get_public_software(page: int = 1, per_page: int = 100) -> str:
        """List public software catalog items available for policies (Addigy API v1).

        API: GET /api/catalog/public

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 100).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN_V1
        try:
            result = await client.get(
                "/api/catalog/public", params={"page": page, "per_page": per_page}
            )
            return json.dumps(result, indent=2)
        except AddigyV1Error as e:
            return f"Error: {e}"
