from __future__ import annotations

import pytest

from maildeskio import Maildesk

BASE_URL = "https://api.maildesk.test"
API_KEY = "sk_test_123"


@pytest.fixture
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def api_key() -> str:
    return API_KEY


@pytest.fixture
def client(httpx_mock):  # type: ignore[no-untyped-def]
    c = Maildesk(api_key=API_KEY, base_url=BASE_URL)
    yield c
    c.close()


@pytest.fixture
def contact_fixture() -> dict:
    return {
        "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "status": "CONFIRMED",
        "tags": ["Newsletter"],
        "createdAt": "2026-04-01T10:00:00.000Z",
    }


@pytest.fixture
def tag_fixture() -> dict:
    return {
        "id": "01HQZTAG00000000000000",
        "name": "Newsletter",
        "description": "Newsletter subscribers",
        "createdAt": "2026-04-01T10:00:00.000Z",
    }
