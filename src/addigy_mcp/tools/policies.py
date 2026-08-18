from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AddigyClient, AddigyError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AddigyClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def addigy_query_policies(
        policies: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional list of policy IDs to filter by; if omitted, "
                    "returns all policies."
                )
            ),
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
        """Query an organization for all policies, or filter to specific policy IDs.

        Use this to look up policy names/IDs — e.g. before calling
        addigy_query_devices with a policy_id filter, or to answer "what
        policies exist for this org".

        API: POST /oa/policies/query
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        body = {"policies": policies} if policies is not None else {}
        params = {"multitenancy": multitenancy, "child-organizations": child_organizations}
        try:
            result = await client.post("/oa/policies/query", json_body=body, params=params)
            return dump_json_capped(result)
        except AddigyError as e:
            return e.to_envelope()
