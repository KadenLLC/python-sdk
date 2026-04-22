"""Tags resource — wraps /api/tags."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional
from urllib.parse import quote

from ._http import HttpClient
from .models import PaginatedTags, Tag, _TagEnvelope


class TagsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self, *, page: Optional[int] = None, limit: Optional[int] = None
    ) -> PaginatedTags:
        data = self._http.request(
            "GET", "/api/tags", params={"page": page, "limit": limit}
        )
        return PaginatedTags.model_validate(data)

    def get(self, tag_id: str) -> Tag:
        data = self._http.request("GET", f"/api/tags/{quote(tag_id, safe='')}")
        return _TagEnvelope.model_validate(data).tag

    def create(self, *, name: str, description: Optional[str] = None) -> Tag:
        body: dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        data = self._http.request("POST", "/api/tags", json=body)
        return _TagEnvelope.model_validate(data).tag

    def update(
        self,
        tag_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tag:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        data = self._http.request("PUT", f"/api/tags/{quote(tag_id, safe='')}", json=body)
        return _TagEnvelope.model_validate(data).tag

    def delete(self, tag_id: str) -> None:
        self._http.request("DELETE", f"/api/tags/{quote(tag_id, safe='')}")

    def list_all(self, *, limit: int = 50) -> Iterator[Tag]:
        page = 1
        seen = 0
        while True:
            result = self.list(page=page, limit=limit)
            yield from result.tags
            seen += len(result.tags)
            if not result.tags or seen >= result.total:
                return
            page += 1
