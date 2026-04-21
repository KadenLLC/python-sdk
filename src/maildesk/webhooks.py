"""Webhook signature verification + typed event payloads."""
from __future__ import annotations

import hmac
import json
import time
from enum import Enum
from hashlib import sha256
from typing import Optional, Union

from pydantic import ConfigDict, Field

from .errors import InvalidSignatureError, StaleWebhookError
from .models import SubscriptionStatus, _BaseModel

WEBHOOK_SIGNATURE_HEADER = "X-Maildesk-Signature"
WEBHOOK_TIMESTAMP_HEADER = "X-Maildesk-Timestamp"


class WebhookEventType(str, Enum):
    SUBSCRIBER_CREATED = "subscriber.created"
    SUBSCRIBER_CONFIRMED = "subscriber.confirmed"
    SUBSCRIBER_UNSUBSCRIBED = "subscriber.unsubscribed"
    SUBSCRIBER_UPDATED = "subscriber.updated"


class ContactEventPayload(_BaseModel):
    """Payload shape for every subscriber.* event."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: WebhookEventType
    event_id: str = Field(alias="eventId")
    id: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: str
    status: Union[SubscriptionStatus, str]
    created_at: str = Field(alias="createdAt")


WebhookEvent = ContactEventPayload


def _parse_signature_header(header: str) -> tuple[int, str]:
    timestamp: Optional[int] = None
    v1: Optional[str] = None
    for part in (p.strip() for p in header.split(",")):
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                continue
        elif key == "v1":
            v1 = value
    if timestamp is None or v1 is None:
        raise InvalidSignatureError("Malformed X-Maildesk-Signature header")
    return timestamp, v1


def verify_webhook(
    *,
    raw_body: Union[str, bytes],
    signature_header: Optional[str],
    secret: str,
    tolerance_seconds: int = 300,
    now_seconds: Optional[int] = None,
) -> ContactEventPayload:
    """Verify a webhook's signature and return the typed event.

    Args:
        raw_body: The raw request body, exactly as received. Do NOT parse JSON first.
        signature_header: Value of the ``X-Maildesk-Signature`` header.
        secret: Your API secret key (same value you use as the Bearer token).
        tolerance_seconds: Reject timestamps older than this. Default 300s. 0 disables.
        now_seconds: Override current time (unix seconds); for testing.

    Raises:
        InvalidSignatureError: If the header is missing, malformed, or the signature
            doesn't match the computed HMAC-SHA256.
        StaleWebhookError: If the signed timestamp is outside the tolerance window.
    """
    if not signature_header:
        raise InvalidSignatureError("Missing X-Maildesk-Signature header")
    if not secret:
        raise InvalidSignatureError("Secret is required")

    timestamp, v1 = _parse_signature_header(signature_header)

    if tolerance_seconds > 0:
        now = now_seconds if now_seconds is not None else int(time.time())
        if abs(now - timestamp) > tolerance_seconds:
            raise StaleWebhookError(
                f"Webhook timestamp {timestamp} is outside tolerance of "
                f"{tolerance_seconds}s from now={now}"
            )

    body_bytes = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    signed_payload = f"{timestamp}.".encode("utf-8") + body_bytes
    expected = hmac.new(secret.encode("utf-8"), signed_payload, sha256).hexdigest()

    if not hmac.compare_digest(expected, v1):
        raise InvalidSignatureError("Signature mismatch")

    try:
        parsed = json.loads(body_bytes)
    except ValueError as exc:
        raise InvalidSignatureError("Webhook body is not valid JSON") from exc

    return ContactEventPayload.model_validate(parsed)
