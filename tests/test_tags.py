from __future__ import annotations

import json

import pytest

from maildeskio import ConflictError


def test_list(httpx_mock, client, base_url, tag_fixture):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags?page=1&limit=50",
        json={"tags": [tag_fixture], "total": 1, "page": 1, "limit": 50},
    )
    res = client.tags.list(page=1, limit=50)
    assert res.tags[0].name == "Newsletter"


def test_get(httpx_mock, client, base_url, tag_fixture):
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/api/tags/{tag_fixture['id']}",
        json={"tag": tag_fixture},
    )
    t = client.tags.get(tag_fixture["id"])
    assert t.id == tag_fixture["id"]


def test_create(httpx_mock, client, base_url, tag_fixture):
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/api/tags",
        status_code=201,
        json={"tag": {**tag_fixture, "name": "Premium", "description": "paid"}},
    )
    t = client.tags.create(name="Premium", description="paid")
    assert t.name == "Premium"

    req = httpx_mock.get_request()
    assert json.loads(req.content) == {"name": "Premium", "description": "paid"}


def test_create_conflict(httpx_mock, client, base_url):
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/api/tags",
        status_code=409,
        json={"statusCode": 409, "message": "Tag name already exists"},
    )
    with pytest.raises(ConflictError):
        client.tags.create(name="Premium")


def test_update(httpx_mock, client, base_url, tag_fixture):
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/api/tags/{tag_fixture['id']}",
        json={"tag": {**tag_fixture, "description": "updated"}},
    )
    t = client.tags.update(tag_fixture["id"], description="updated")
    assert t.description == "updated"

    req = httpx_mock.get_request()
    assert json.loads(req.content) == {"description": "updated"}


def test_delete(httpx_mock, client, base_url, tag_fixture):
    httpx_mock.add_response(
        method="DELETE",
        url=f"{base_url}/api/tags/{tag_fixture['id']}",
        status_code=204,
    )
    assert client.tags.delete(tag_fixture["id"]) is None
