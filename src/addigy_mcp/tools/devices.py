import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool()
    async def addigy_query_devices(
        page: int | None = None,
        per_page: int | None = None,
        search_any: str | None = None,
        policy_id: str | None = None,
        filters: list[dict] | None = None,
        desired_fact_identifiers: list[str] | None = None,
        sort_field: str | None = None,
        sort_direction: str | None = None,
    ) -> str:
        """Universal search for devices in the organization by device-fact values.

        API: POST /devices

        Args:
            page: Page number (default 1).
            per_page: Results per page (default 10).
            search_any: Free-text search across devices.
            policy_id: Filter devices assigned to this policy ID.
            filters: List of filter objects, each shaped like
                {"audit_field": "device_model_name", "operation": "contains",
                "type": "string", "value": ..., "range_value": ...}.
            desired_fact_identifiers: List of device-fact identifiers to
                include in the response.
            sort_field: Field to sort by (e.g. "serial_number").
            sort_direction: "asc" or "desc".
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        query: dict = {}
        if search_any is not None:
            query["search_any"] = search_any
        if policy_id is not None:
            query["policy_id"] = policy_id
        if filters is not None:
            query["filters"] = filters
        body = {
            "page": page,
            "per_page": per_page,
            "desired_fact_identifiers": desired_fact_identifiers,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }
        if query:
            body["query"] = query
        body = {k: v for k, v in body.items() if v is not None}
        try:
            result = await client.post("/devices", json_body=body)
            return json.dumps(result, indent=2)
        except AddigyError as e:
            return f"Error: {e}"
