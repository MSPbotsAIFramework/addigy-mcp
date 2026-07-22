import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool()
    async def addigy_query_installed_apps_agent(
        agent_ids: list[str],
        sort_field: str,
        sort_direction: str,
        names: list[str] | None = None,
        page: int | None = None,
        per_page: int | None = None,
        multitenancy: bool | None = None,
        child_organizations: str | None = None,
    ) -> str:
        """Query installed applications reported by the Addigy agent (macOS only).

        API: POST /oa/installed-apps/agent/query

        Args:
            agent_ids: Required list of agent (device) IDs to query.
            sort_field: Required sort field ("agent_id" or "name").
            sort_direction: Required sort direction ("asc" or "desc").
            names: Optional list of application names to filter by.
            page: Page number (default 1).
            per_page: Results per page (max 100, default 10).
            multitenancy: If true, include data for all descendant (child)
                organizations.
            child_organizations: Comma-separated list of organization IDs to
                restrict results to when `multitenancy` is true.
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
        agent_ids: list[str],
        limit: int,
        skip: int,
        sort_direction: str,
        sort_field: str,
        multitenancy: bool | None = None,
        child_organizations: str | None = None,
    ) -> str:
        """Query installed applications reported via MDM.

        API: POST /oa/installed-apps/mdm/query

        Args:
            agent_ids: Required list of agent (device) IDs to query.
            limit: Required max number of results to return.
            skip: Required number of results to skip (for pagination).
            sort_direction: Required sort direction ("asc" or "desc").
            sort_field: Required sort field (e.g. "last_updated").
            multitenancy: If true, include data for all descendant (child)
                organizations.
            child_organizations: Comma-separated list of organization IDs to
                restrict results to when `multitenancy` is true.
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
