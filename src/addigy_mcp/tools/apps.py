import json
from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool()
    async def addigy_query_installed_apps_agent(
        agent_ids: Annotated[
            list[str], Field(description="Required list of agent (device) IDs to query.")
        ],
        sort_field: Annotated[
            str, Field(description='Required sort field ("agent_id" or "name").')
        ],
        sort_direction: Annotated[
            str, Field(description='Required sort direction ("asc" or "desc").')
        ],
        names: Annotated[
            list[str] | None,
            Field(description="Optional list of application names to filter by."),
        ] = None,
        page: Annotated[int | None, Field(description="Page number (default 1).")] = None,
        per_page: Annotated[
            int | None, Field(description="Results per page (max 100, default 10).")
        ] = None,
        multitenancy: Annotated[
            bool | None,
            Field(
                description="If true, include data for all descendant (child) organizations."
            ),
        ] = None,
        child_organizations: Annotated[
            str | None,
            Field(
                description=(
                    "Comma-separated list of organization IDs to restrict results to "
                    "when `multitenancy` is true."
                )
            ),
        ] = None,
    ) -> str:
        """Query installed applications reported by the Addigy agent (macOS only).

        Use this for devices enrolled via the native Addigy agent. For
        devices enrolled only through MDM (no Addigy agent installed), use
        addigy_query_installed_apps_mdm instead — the two report from
        different data sources and cover different device populations.

        API: POST /oa/installed-apps/agent/query
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        query: dict = {"agent_ids": agent_ids}
        if names is not None:
            query["names"] = names
        body = {
            "query": query,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
            "page": page,
            "per_page": per_page,
        }
        body = {k: v for k, v in body.items() if v is not None}
        params = {"multitenancy": multitenancy, "child-organizations": child_organizations}
        try:
            result = await client.post(
                "/oa/installed-apps/agent/query", json_body=body, params=params
            )
            return json.dumps(result, indent=2)
        except AddigyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def addigy_query_installed_apps_mdm(
        agent_ids: Annotated[
            list[str], Field(description="Required list of agent (device) IDs to query.")
        ],
        limit: Annotated[
            int, Field(description="Required max number of results to return.")
        ],
        skip: Annotated[
            int, Field(description="Required number of results to skip (for pagination).")
        ],
        sort_direction: Annotated[
            str, Field(description='Required sort direction ("asc" or "desc").')
        ],
        sort_field: Annotated[
            str, Field(description='Required sort field (e.g. "last_updated").')
        ],
        multitenancy: Annotated[
            bool | None,
            Field(
                description="If true, include data for all descendant (child) organizations."
            ),
        ] = None,
        child_organizations: Annotated[
            str | None,
            Field(
                description=(
                    "Comma-separated list of organization IDs to restrict results to "
                    "when `multitenancy` is true."
                )
            ),
        ] = None,
    ) -> str:
        """Query installed applications reported via MDM.

        Use this for devices managed only through MDM enrollment (works even
        without the native Addigy agent installed). For devices that do have
        the Addigy agent, addigy_query_installed_apps_agent is the source
        Addigy itself considers authoritative.

        API: POST /oa/installed-apps/mdm/query
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {
            "agent_ids": agent_ids,
            "limit": limit,
            "skip": skip,
            "sort_direction": sort_direction,
            "sort_field": sort_field,
        }
        params = {"multitenancy": multitenancy, "child-organizations": child_organizations}
        try:
            result = await client.post(
                "/oa/installed-apps/mdm/query", json_body=body, params=params
            )
            return json.dumps(result, indent=2)
        except AddigyError as e:
            return f"Error: {e}"
