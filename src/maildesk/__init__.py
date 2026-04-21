"""Official Python SDK for the Maildesk API."""
from __future__ import annotations

from .client import Maildesk
from .contacts import ContactsResource
from .errors import (
    AuthenticationError,
    ConflictError,
    InvalidSignatureError,
    MaildeskError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    StaleWebhookError,
    ValidationError,
)
from .models import (
    BulkContactFailure,
    BulkContactFailureReason,
    BulkContactResult,
    Contact,
    PaginatedContacts,
    PaginatedTags,
    SubscriptionStatus,
    Tag,
)
from .tags import TagsResource
from .webhooks import (
    WEBHOOK_SIGNATURE_HEADER,
    WEBHOOK_TIMESTAMP_HEADER,
    ContactEventPayload,
    WebhookEvent,
    WebhookEventType,
    verify_webhook,
)

__version__ = "0.1.0"

__all__ = [
    "Maildesk",
    "ContactsResource",
    "TagsResource",
    # Models
    "Contact",
    "Tag",
    "BulkContactFailure",
    "BulkContactFailureReason",
    "BulkContactResult",
    "PaginatedContacts",
    "PaginatedTags",
    "SubscriptionStatus",
    # Webhooks
    "verify_webhook",
    "WebhookEvent",
    "WebhookEventType",
    "ContactEventPayload",
    "WEBHOOK_SIGNATURE_HEADER",
    "WEBHOOK_TIMESTAMP_HEADER",
    # Errors
    "MaildeskError",
    "AuthenticationError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "InvalidSignatureError",
    "StaleWebhookError",
]
