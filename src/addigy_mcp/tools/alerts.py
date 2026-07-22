import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool()
    async def addigy_get_alerts(
        page: str,
        per_page: str,
        status: str | None = None,
    ) -> str:
        """Query the list of received monitoring alerts.

        API: GET /monitoring/received-alerts

        Args:
            page: Required page number (as a string, per the vendor API).
            per_page: Required results per page (as a string, per the vendor API).
            status: Optional filter by alert status.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"page": page, "per_page": per_page, "status": status}
        try:
            result = await client.get("/monitoring/received-alerts", params=params)
            return json.dumps(result, indent=2)
        except AddigyError as e:
            return f"Error: {e}"
