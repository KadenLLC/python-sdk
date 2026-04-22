# maildeskio

Official Python SDK for the [Maildesk](https://maildesk.io) API. Typed, `mypy --strict` Python 3.9+.

Covers:

- **Contacts** — list, get, create, bulk create (with partial-failure reporting), update, delete, auto-paginate
- **Tags** — list, get, create, update, delete, auto-paginate
- **Webhooks** — HMAC-SHA256 signature verification + typed event payloads

Built on [httpx](https://www.python-httpx.org/) and [Pydantic v2](https://docs.pydantic.dev/).

## Install

```bash
pip install maildeskio
```

## Quick start

```python
from maildeskio import Maildesk

client = Maildesk(api_key="sk_live_...")

contact = client.contacts.create(
    email="jane@example.com",
    first_name="Jane",
    last_name="Doe",
    is_confirmed=True,
    tags=["01HQZTAG00000000000000"],
)

print(contact.id, contact.email)
```

Use it as a context manager to close the underlying connection pool:

```python
with Maildesk(api_key="sk_live_...") as client:
    for c in client.contacts.list_all():
        print(c.email)
```

## Authentication

Generate an API secret key from the Maildesk dashboard under **Developer → API keys** and pass it as `api_key`. The SDK sends it as a Bearer token on every request.

## Configuration

| Parameter  | Type  | Default                 | Notes                                  |
| ---------- | ----- | ----------------------- | -------------------------------------- |
| `api_key`  | str   | —                       | **Required.** Your secret key.         |
| `base_url` | str   | `http://localhost:3000` | Point at your Maildesk deployment.     |
| `timeout`  | float | `30.0`                  | Per-request timeout in seconds.        |

## Contacts

```python
# List (paginated)
result = client.contacts.list(page=1, limit=50)
print(result.total, [c.email for c in result.subscribers])

# Get one
contact = client.contacts.get("01ARZ3NDEKTSV4RRFFQ69G5FAV")

# Create
created = client.contacts.create(
    email="new@example.com",
    first_name="New",
    last_name="Person",
    is_confirmed=True,
    tags=["01HQZTAG00000000000000"],
)

# Update (partial)
updated = client.contacts.update(created.id, first_name="Renamed")

# Delete
client.contacts.delete(created.id)

# Auto-paginate every contact
for c in client.contacts.list_all(limit=100):
    print(c.email)
```

### Bulk create — partial failures

`bulk_create` accepts up to **100 contacts per call** and returns a result with a `failed` list giving per-item reasons. A fully successful batch has an empty `failed` list.

```python
from maildeskio import BulkContactFailureReason

result = client.contacts.bulk_create([
    {"email": "a@example.com", "first_name": "A", "last_name": "Z"},
    {"email": "dup@example.com", "first_name": "D", "last_name": "U"},
])

for failure in result.failed:
    if failure.reason is BulkContactFailureReason.EMAIL_ALREADY_EXISTS:
        pass  # already in the database
    elif failure.reason is BulkContactFailureReason.DUPLICATE_IN_REQUEST:
        pass  # two rows in the same batch had the same email
    else:  # INTERNAL_ERROR
        pass  # retry
```

## Tags

```python
result = client.tags.list()
tag = client.tags.create(name="Newsletter", description="Weekly list")
client.tags.update(tag.id, description="Updated")
client.tags.delete(tag.id)

for t in client.tags.list_all():
    print(t.name)
```

Tag names are unique per business — creating a duplicate raises `ConflictError`.

## Webhooks

Maildesk signs every outbound webhook with HMAC-SHA256 using your API secret. Use `verify_webhook` to validate signatures and get a typed event.

**Event types:**

- `subscriber.created`
- `subscriber.confirmed`
- `subscriber.unsubscribed`
- `subscriber.updated`

### FastAPI example

```python
import os
from fastapi import FastAPI, Request, HTTPException

from maildeskio import verify_webhook, InvalidSignatureError, StaleWebhookError, WebhookEventType

app = FastAPI()
SECRET = os.environ["MAILDESK_WEBHOOK_SECRET"]


@app.post("/webhooks/maildesk")
async def maildesk_webhook(request: Request):
    raw_body = await request.body()  # bytes — do NOT parse JSON first
    try:
        event = verify_webhook(
            raw_body=raw_body,
            signature_header=request.headers.get("X-Maildesk-Signature"),
            secret=SECRET,
        )
    except (InvalidSignatureError, StaleWebhookError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if event.type is WebhookEventType.SUBSCRIBER_UNSUBSCRIBED:
        # ...
        pass

    return {"ok": True}
```

### Flask example

```python
from flask import Flask, request, abort
from maildeskio import verify_webhook, InvalidSignatureError, StaleWebhookError

app = Flask(__name__)


@app.post("/webhooks/maildesk")
def maildesk_webhook():
    try:
        event = verify_webhook(
            raw_body=request.get_data(),  # raw bytes
            signature_header=request.headers.get("X-Maildesk-Signature"),
            secret=app.config["MAILDESK_WEBHOOK_SECRET"],
        )
    except (InvalidSignatureError, StaleWebhookError) as exc:
        abort(400, str(exc))

    # ... process event.type, event.email, event.event_id
    return "ok"
```

### Options

```python
verify_webhook(
    raw_body=...,           # bytes or str — raw request body
    signature_header=...,   # value of X-Maildesk-Signature
    secret=...,             # your API secret key
    tolerance_seconds=300,  # default — reject timestamps older than 5 minutes. 0 disables.
)
```

### Idempotency

Every event has a unique `event_id`. Retries (e.g. after your endpoint returns 5xx) reuse the same `event_id`, so persist it to skip duplicates:

```python
event = verify_webhook(...)
if seen_event_ids.contains(event.event_id):
    return
seen_event_ids.add(event.event_id)
# process event
```

## Error handling

All SDK errors inherit from `MaildeskError` and carry `status_code`, `body`, and an optional `request_id`.

| Exception               | Trigger                                    |
| ----------------------- | ------------------------------------------ |
| `AuthenticationError`   | 401 — missing/invalid API key              |
| `NotFoundError`         | 404 — resource not found                   |
| `ConflictError`         | 409 — unique-constraint violation          |
| `ValidationError`       | 400 / 422 — request invalid                |
| `RateLimitError`        | 429 — includes `retry_after` seconds       |
| `ServerError`           | 5xx                                        |
| `NetworkError`          | transport-level failure                    |
| `InvalidSignatureError` | webhook signature mismatch                 |
| `StaleWebhookError`     | webhook timestamp outside tolerance window |

```python
from maildeskio import RateLimitError
import time

try:
    client.contacts.create(email=..., first_name=..., last_name=...)
except RateLimitError as e:
    if e.retry_after:
        time.sleep(e.retry_after)
        # retry
    raise
```

The server enforces **120 requests per 60 seconds per API key** — back off on 429.

## Typing

The SDK ships a `py.typed` marker; all public methods are annotated. You can run `mypy --strict` against your code and get full type-checking through the SDK boundary. Responses are Pydantic v2 models, so you can use `.model_dump()` / `.model_dump_json()` on any returned object.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest              # runs the test suite with pytest-httpx
mypy src/           # strict type-checking
ruff check .        # lint
```

## License

MIT
