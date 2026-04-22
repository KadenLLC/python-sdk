"""Exception hierarchy for the Maildesk SDK."""
from __future__ import annotations

from typing import Any, Optional


class MaildeskError(Exception):
    """Base class for every Maildesk SDK error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Any = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body
        self.request_id = request_id


class AuthenticationError(MaildeskError):
    """Raised on HTTP 401."""


class NotFoundError(MaildeskError):
    """Raised on HTTP 404."""


class ConflictError(MaildeskError):
    """Raised on HTTP 409 (e.g. duplicate tag name)."""


class ValidationError(MaildeskError):
    """Raised on HTTP 400 or 422 (request validation failed)."""


class RateLimitError(MaildeskError):
    """Raised on HTTP 429. `retry_after` is the server's Retry-After in seconds, if present."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Any = None,
        request_id: Optional[str] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(
            message, status_code=status_code, body=body, request_id=request_id
        )
        self.retry_after = retry_after


class ServerError(MaildeskError):
    """Raised on HTTP 5xx."""


class NetworkError(MaildeskError):
    """Raised when the HTTP transport itself fails (DNS, timeout, connection reset)."""


class InvalidSignatureError(MaildeskError):
    """Raised when a webhook signature fails to verify."""


class StaleWebhookError(MaildeskError):
    """Raised when a webhook timestamp is outside the tolerance window."""
