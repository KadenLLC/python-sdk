"""Contacts resource — wraps /api/subscribers."""
from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any, Optional
from urllib.parse import quote

from ._http import HttpClient
from .models import (
    BulkContactResult,
    Contact,
    PaginatedContacts,
    _ContactEnvelope,
)


class ContactsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self, *, page: Optional[int] = None, limit: Optional[int] = None
    ) -> PaginatedContacts:
        data = self._http.request(
            "GET",
            "/api/subscribers",
            params={"page": page, "limit": limit},
        )
        return PaginatedContacts.model_validate(data)

    def get(self, contact_id: str) -> Contact:
        data = self._http.request("GET", f"/api/subscribers/{quote(contact_id, safe='')}")
        return _ContactEnvelope.model_validate(data).subscriber

    def create(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        is_confirmed: bool = False,
        tags: Optional[builtins.list[str]] = None,
    ) -> Contact:
        body = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "isConfirmed": is_confirmed,
            "tags": tags or [],
        }
        data = self._http.request("POST", "/api/subscribers", json=body)
        return _ContactEnvelope.model_validate(data).subscriber

    def bulk_create(self, subscribers: builtins.list[dict[str, Any]]) -> BulkContactResult:
        """Create up to 100 contacts in one request.

        Each item in ``subscribers`` should contain: ``email``, ``first_name``,
        ``last_name``, and optionally ``is_confirmed`` and ``tags``.
        """
        body = {
            "subscribers": [
                {
                    "email": s["email"],
                    "firstName": s["first_name"],
                    "lastName": s["last_name"],
                    "isConfirmed": s.get("is_confirmed", False),
                    "tags": s.get("tags", []),
                }
                for s in subscribers
            ]
        }
        data = self._http.request("POST", "/api/subscribers/bulk", json=body)
        return BulkContactResult.model_validate(data)

    def update(
        self,
        contact_id: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        tags: Optional[builtins.list[str]] = None,
    ) -> Contact:
        body: dict[str, Any] = {}
        if first_name is not None:
            body["firstName"] = first_name
        if last_name is not None:
            body["lastName"] = last_name
        if tags is not None:
            body["tags"] = tags
        data = self._http.request(
            "PUT", f"/api/subscribers/{quote(contact_id, safe='')}", json=body
        )
        return _ContactEnvelope.model_validate(data).subscriber

    def delete(self, contact_id: str) -> None:
        self._http.request("DELETE", f"/api/subscribers/{quote(contact_id, safe='')}")

    def list_all(self, *, limit: int = 50) -> Iterator[Contact]:
        """Yield every contact, walking pages until exhausted."""
        page = 1
        seen = 0
        while True:
            result = self.list(page=page, limit=limit)
            yield from result.subscribers
            seen += len(result.subscribers)
            if not result.subscribers or seen >= result.total:
                return
            page += 1
