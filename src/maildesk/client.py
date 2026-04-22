"""Maildesk client — the entry point."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from ._http import HttpClient
from .contacts import ContactsResource
from .tags import TagsResource


class Maildesk:
    """Synchronous Maildesk API client.

    Example:
        >>> client = Maildesk(api_key="sk_live_...")
        >>> contact = client.contacts.create(
        ...     email="jane@example.com",
        ...     first_name="Jane",
        ...     last_name="Doe",
        ...     is_confirmed=True,
        ... )
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._http = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            transport=transport,
        )
        self.contacts = ContactsResource(self._http)
        self.tags = TagsResource(self._http)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> Maildesk:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
