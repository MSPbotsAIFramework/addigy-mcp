from typing import Any

import httpx


class AddigyV1Error(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Addigy API v1 error {status_code}: {message}")


class AddigyV1Client:
    """Async httpx client wrapping the legacy Addigy API v1.

    Every Addigy v1 organization is hosted on its own "Site" domain, and
    auth is via client_id/client_secret passed as query-string parameters
    on every request (per Addigy's own v1 API documentation examples).
    """

    def __init__(self, client_id: str, client_secret: str, site: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = f"https://{site.replace('https://', '').replace('http://', '').rstrip('/')}"

    def _clean_params(self, params: dict | None) -> dict:
        base = {"client_id": self._client_id, "client_secret": self._client_secret}
        if params:
            base.update({k: v for k, v in params.items() if v is not None})
        return base

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}{path}",
                    params=self._clean_params(params),
                )
            except httpx.RequestError as e:
                raise AddigyV1Error(0, f"{e or type(e).__name__} (url={self._base_url}{path})") from e
            self._raise_for_status(resp)
            return self._parse_body(resp)

    def _parse_body(self, resp: httpx.Response) -> Any:
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
                if isinstance(detail, dict):
                    msg = detail.get("message") or detail.get("error") or str(detail)
                else:
                    msg = str(detail)
            except ValueError:
                msg = resp.text
            raise AddigyV1Error(resp.status_code, msg)
