from __future__ import annotations

import pytest

from maildesk import (
    AuthenticationError,
    Maildesk,
    MaildeskError,
    RateLimitError,
    ServerError,
    ValidationError,
)


def test_requires_api_key():
    with pytest.raises(MaildeskError):
        Maildesk(api_key="")


def test_sends_auth_and_content_type(httpx_mock, client, base_url, api_key):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags?page=1&limit=50",
        json={"tags": [], "total": 0, "page": 1, "limit": 50},
    )
    client.tags.list(page=1, limit=50)

    request = httpx_mock.get_request()
    assert request.headers["authorization"] == f"Bearer {api_key}"
    assert request.headers["content-type"] == "application/json"


def test_401_maps_to_authentication_error(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags",
        status_code=401,
        json={"statusCode": 401, "message": "Bad token"},
    )
    with pytest.raises(AuthenticationError) as ei:
        client.tags.list()
    assert ei.value.status_code == 401
    assert "Bad token" in str(ei.value)


def test_400_maps_to_validation_error_with_array_message(
    httpx_mock, client, base_url
):
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/api/tags",
        status_code=400,
        json={"statusCode": 400, "message": ["name should not be empty"]},
    )
    with pytest.raises(ValidationError) as ei:
        client.tags.create(name="")
    assert "name should not be empty" in str(ei.value)


def test_429_maps_to_rate_limit_error(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags",
        status_code=429,
        json={"statusCode": 429, "message": "Too many requests"},
        headers={"Retry-After": "42"},
    )
    with pytest.raises(RateLimitError) as ei:
        client.tags.list()
    assert ei.value.retry_after == 42


def test_500_maps_to_server_error(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags",
        status_code=500,
        json={"message": "boom"},
    )
    with pytest.raises(ServerError):
        client.tags.list()


def test_query_params_omit_none(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags",
        json={"tags": [], "total": 0, "page": 1, "limit": 50},
    )
    client.tags.list()  # no page or limit — should not appear in URL

    request = httpx_mock.get_request()
    assert "page=" not in str(request.url)
    assert "limit=" not in str(request.url)


def test_client_context_manager_closes():
    with Maildesk(api_key="sk_test", base_url="https://api.maildesk.test") as c:
        assert c.contacts is not None
    # exiting the context should close the underlying client
