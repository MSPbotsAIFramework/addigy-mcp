from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN

_MAX_PER_PAGE = 200


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def addigy_get_alerts(
        page: Annotated[
            str, Field(description="Required page number (as a string, per the vendor API).")
        ],
        per_page: Annotated[
            str,
            Field(
                description=(
                    "Required results per page (as a string, per the vendor API, "
                    "capped at 200)."
                )
            ),
        ],
        status: Annotated[
            str | None,
            Field(
                description=(
                    "Optional filter by alert status. Addigy's alert lifecycle "
                    'documentation describes these states: "Unattended" (newly '
                    'triggered, needs action), "Acknowledged" (temporarily muted), '
                    '"Resolved" (permanently closed), "Closed" (closed, will '
                    "re-arm if it recurs) — but the exact query-string casing/values "
                    "this endpoint expects aren't independently confirmed against "
                    "the live API, so omit this filter and check status client-side "
                    "if a call with it returns unexpected results."
                )
            ),
        ] = None,
    ) -> str:
        """Query the list of received monitoring alerts.

        Use this for questions like "what alerts fired recently" or "any open
        alerts for this org" — Addigy's monitoring/compliance notifications,
        not device inventory (use addigy_query_devices for that).

        API: GET /monitoring/received-alerts
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            per_page_int = int(per_page)
        except ValueError:
            per_page_int = None
        if per_page_int is not None and per_page_int > _MAX_PER_PAGE:
            per_page = str(_MAX_PER_PAGE)
        params = {"page": page, "per_page": per_page, "status": status}
        try:
            result = await client.get("/monitoring/received-alerts", params=params)
            return dump_json_capped(result)
        except AddigyError as e:
            return e.to_envelope()
