from __future__ import annotations

import json

import pytest

from maildeskio import BulkContactFailureReason, NotFoundError, SubscriptionStatus


def test_list_sends_pagination_and_auth(httpx_mock, client, base_url, api_key, contact_fixture):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/subscribers?page=2&limit=25",
        json={"subscribers": [contact_fixture], "total": 1, "page": 2, "limit": 25},
    )

    res = client.contacts.list(page=2, limit=25)

    assert res.total == 1
    assert res.subscribers[0].email == "john@example.com"
    assert res.subscribers[0].status is SubscriptionStatus.CONFIRMED

    request = httpx_mock.get_request()
    assert request.headers["authorization"] == f"Bearer {api_key}"


def test_get_unwraps_subscriber(httpx_mock, client, base_url, contact_fixture):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/subscribers/{contact_fixture['id']}",
        json={"subscriber": contact_fixture},
    )

    c = client.contacts.get(contact_fixture["id"])
    assert c.id == contact_fixture["id"]
    assert c.first_name == "John"


def test_create_sends_defaults(httpx_mock, client, base_url, contact_fixture):
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/api/subscribers",
        json={"subscriber": contact_fixture},
        status_code=201,
    )

    c = client.contacts.create(
        email="new@example.com", first_name="New", last_name="Person"
    )
    assert c.id == contact_fixture["id"]

    request = httpx_mock.get_request()
    sent = json.loads(request.content)
    assert sent == {
        "email": "new@example.com",
        "firstName": "New",
        "lastName": "Person",
        "isConfirmed": False,
        "tags": [],
    }


def test_bulk_create_returns_failed(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/api/subscribers/bulk",
        json={
            "failed": [
                {
                    "index": 1,
                    "email": "dup@example.com",
                    "reason": "EMAIL_ALREADY_EXISTS",
                }
            ]
        },
    )

    result = client.contacts.bulk_create(
        [
            {"email": "a@example.com", "first_name": "A", "last_name": "Z"},
            {"email": "dup@example.com", "first_name": "D", "last_name": "U"},
        ]
    )
    assert len(result.failed) == 1
    assert result.failed[0].reason is BulkContactFailureReason.EMAIL_ALREADY_EXISTS

    request = httpx_mock.get_request()
    sent = json.loads(request.content)
    assert sent["subscribers"][0]["firstName"] == "A"


def test_update_sends_partial_body(httpx_mock, client, base_url, contact_fixture):
    updated = {**contact_fixture, "firstName": "Renamed"}
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/api/subscribers/{contact_fixture['id']}",
        json={"subscriber": updated},
    )

    c = client.contacts.update(contact_fixture["id"], first_name="Renamed")
    assert c.first_name == "Renamed"

    request = httpx_mock.get_request()
    assert json.loads(request.content) == {"firstName": "Renamed"}


def test_delete_returns_none(httpx_mock, client, base_url, contact_fixture):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{base_url}/api/subscribers/{contact_fixture['id']}",
        status_code=204,
    )
    assert client.contacts.delete(contact_fixture["id"]) is None


def test_get_raises_not_found(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/subscribers/missing",
        status_code=404,
        json={"statusCode": 404, "message": "Contact not found"},
    )
    with pytest.raises(NotFoundError) as ei:
        client.contacts.get("missing")
    assert ei.value.status_code == 404
    assert "Contact not found" in str(ei.value)


def test_list_all_walks_pages(httpx_mock, client, base_url, contact_fixture):
    page1 = [
        {**contact_fixture, "id": "p1-0", "email": "p1-0@example.com"},
        {**contact_fixture, "id": "p1-1", "email": "p1-1@example.com"},
    ]
    page2 = [{**contact_fixture, "id": "p2-0", "email": "p2-0@example.com"}]

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/subscribers?page=1&limit=2",
        json={"subscribers": page1, "total": 3, "page": 1, "limit": 2},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/subscribers?page=2&limit=2",
        json={"subscribers": page2, "total": 3, "page": 2, "limit": 2},
    )

    ids = [c.id for c in client.contacts.list_all(limit=2)]
    assert ids == ["p1-0", "p1-1", "p2-0"]
