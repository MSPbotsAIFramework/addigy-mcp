import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool()
    async def addigy_query_policies(
        policies: list[str] | None = None,
        multitenancy: bool | None = None,
        child_organizations: str | None = None,
    ) -> str:
        """Query an organization for all policies, or filter to specific policy IDs.

        API: POST /oa/policies/query

        Args:
            policies: Optional list of policy IDs to filter by; if omitted,
                returns all policies.
            multitenancy: If true, include data for all descendant (child)
                organizations.
            child_organizations: Comma-separated list of organization IDs to
                restrict results to when `multitenancy` is true.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {"policies": policies} if policies is not None else {}
        params = {"multitenancy": multitenancy, "child-organizations": child_organizations}
        try:
            result = await client.post("/oa/policies/query", json_body=body, params=params)
            return json.dumps(result, indent=2)
        except AddigyError as e:
            return f"Error: {e}"
