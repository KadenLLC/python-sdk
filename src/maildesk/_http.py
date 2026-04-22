"""HTTP transport wrapping httpx.Client with Maildesk auth and error mapping."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from .errors import (
    AuthenticationError,
    ConflictError,
    MaildeskError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_TIMEOUT_SECONDS = 30.0


class HttpClient:
    """Thin wrapper around ``httpx.Client`` that injects Bearer auth and maps errors."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        if not api_key:
            raise MaildeskError("api_key is required")
        self._client = httpx.Client(
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
    ) -> Any:
        clean_params: Optional[dict[str, Any]] = None
        if params is not None:
            clean_params = {k: v for k, v in params.items() if v is not None}

        try:
            response = self._client.request(
                method, path, params=clean_params, json=json
            )
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc) or "Network request failed") from exc

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        request_id = response.headers.get("x-request-id")

        if 200 <= status < 300:
            if status == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return None

        try:
            body: Any = response.json()
        except ValueError:
            body = response.text

        message = _extract_message(body) or f"Request failed with status {status}"
        common = {"status_code": status, "body": body, "request_id": request_id}

        if status == 401:
            raise AuthenticationError(message, **common)
        if status == 404:
            raise NotFoundError(message, **common)
        if status == 409:
            raise ConflictError(message, **common)
        if status in (400, 422):
            raise ValidationError(message, **common)
        if status == 429:
            retry_after = _parse_retry_after(response.headers.get("retry-after"))
            raise RateLimitError(message, retry_after=retry_after, **common)
        if status >= 500:
            raise ServerError(message, **common)
        raise MaildeskError(message, **common)


def _extract_message(body: Any) -> Optional[str]:
    if not isinstance(body, dict):
        return None
    m = body.get("message")
    if isinstance(m, str):
        return m
    if isinstance(m, list):
        return "; ".join(str(x) for x in m if isinstance(x, str))
    return None


def _parse_retry_after(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
