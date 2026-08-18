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
    async def addigy_query_devices(
        page: Annotated[int | None, Field(description="Page number (default 1).")] = None,
        per_page: Annotated[
            int | None, Field(description="Results per page (default 10, max 200).")
        ] = None,
        search_any: Annotated[
            str | None, Field(description="Free-text search across devices.")
        ] = None,
        policy_id: Annotated[
            str | None, Field(description="Filter devices assigned to this policy ID.")
        ] = None,
        filters: Annotated[
            list[dict] | None,
            Field(
                description=(
                    "List of filter objects, each shaped like "
                    '{"audit_field": "device_model_name", "operation": "contains", '
                    '"type": "string", "value": ..., "range_value": ...}. Other '
                    'confirmed examples from Addigy\'s docs: {"audit_field": "online", '
                    '"operation": "=", "type": "boolean", "value": "true"} and '
                    '{"audit_field": "policy_id", "operation": "contains", '
                    '"type": "list", "value": [...]}. Addigy does not publicly '
                    "enumerate the full audit_field/operation/type vocabulary beyond "
                    "these documented examples — if a specific fact isn't one of "
                    "them, prefer search_any for a free-text lookup instead of "
                    "guessing a field name."
                )
            ),
        ] = None,
        desired_fact_identifiers: Annotated[
            list[str] | None,
            Field(
                description="List of device-fact identifiers to include in the response."
            ),
        ] = None,
        sort_field: Annotated[
            str | None, Field(description='Field to sort by (e.g. "serial_number").')
        ] = None,
        sort_direction: Annotated[
            str | None, Field(description='"asc" or "desc".')
        ] = None,
    ) -> str:
        """Universal search for devices in the organization by device-fact values.

        Use this for questions about a customer's Mac/iOS fleet — device
        inventory, model/OS breakdowns, which devices are on a given policy,
        or a free-text lookup by serial number/hostname.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if per_page is not None:
            per_page = min(per_page, _MAX_PER_PAGE)
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
            return dump_json_capped(result)
        except AddigyError as e:
            return e.to_envelope()
