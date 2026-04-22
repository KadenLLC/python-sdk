from __future__ import annotations

import hmac
import json
import time
from hashlib import sha256

import pytest

from maildeskio import (
    InvalidSignatureError,
    StaleWebhookError,
    WebhookEventType,
    verify_webhook,
)

SECRET = "whsec_topsecret"


def _sign(body: str, timestamp: int, secret: str = SECRET) -> str:
    signed = f"{timestamp}.{body}".encode()
    sig = hmac.new(secret.encode("utf-8"), signed, sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def _valid_body() -> str:
    return json.dumps(
        {
            "type": "subscriber.created",
            "eventId": "evt_01HABC",
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "status": "CONFIRMED",
            "createdAt": "2026-04-01T10:00:00.000Z",
        }
    )


def test_valid_signature_returns_parsed_event():
    body = _valid_body()
    ts = int(time.time())
    event = verify_webhook(
        raw_body=body,
        signature_header=_sign(body, ts),
        secret=SECRET,
    )
    assert event.type is WebhookEventType.SUBSCRIBER_CREATED
    assert event.email == "john@example.com"
    assert event.event_id == "evt_01HABC"


def test_accepts_bytes_body():
    body = _valid_body()
    ts = int(time.time())
    event = verify_webhook(
        raw_body=body.encode("utf-8"),
        signature_header=_sign(body, ts),
        secret=SECRET,
    )
    assert event.event_id == "evt_01HABC"


def test_rejects_tampered_body():
    body = _valid_body()
    ts = int(time.time())
    sig = _sign(body, ts)
    tampered = body.replace("John", "Jane")
    with pytest.raises(InvalidSignatureError):
        verify_webhook(raw_body=tampered, signature_header=sig, secret=SECRET)


def test_rejects_wrong_secret():
    body = _valid_body()
    ts = int(time.time())
    with pytest.raises(InvalidSignatureError):
        verify_webhook(
            raw_body=body,
            signature_header=_sign(body, ts, "wrong_secret"),
            secret=SECRET,
        )


def test_rejects_stale_timestamp():
    body = _valid_body()
    now = 1_700_000_000
    ts_old = now - 600
    with pytest.raises(StaleWebhookError):
        verify_webhook(
            raw_body=body,
            signature_header=_sign(body, ts_old),
            secret=SECRET,
            tolerance_seconds=300,
            now_seconds=now,
        )


def test_tolerance_zero_disables_check():
    body = _valid_body()
    now = 1_700_000_000
    ts_old = now - 999_999
    event = verify_webhook(
        raw_body=body,
        signature_header=_sign(body, ts_old),
        secret=SECRET,
        tolerance_seconds=0,
        now_seconds=now,
    )
    assert event.type is WebhookEventType.SUBSCRIBER_CREATED


def test_rejects_malformed_header():
    with pytest.raises(InvalidSignatureError):
        verify_webhook(
            raw_body=_valid_body(), signature_header="garbage", secret=SECRET
        )


def test_rejects_missing_header():
    with pytest.raises(InvalidSignatureError):
        verify_webhook(raw_body=_valid_body(), signature_header=None, secret=SECRET)


def test_rejects_empty_secret():
    body = _valid_body()
    ts = int(time.time())
    with pytest.raises(InvalidSignatureError):
        verify_webhook(
            raw_body=body, signature_header=_sign(body, ts), secret=""
        )
