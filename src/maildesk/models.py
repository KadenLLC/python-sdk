"""Pydantic models for Maildesk API request/response payloads."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    PERMANENT_BOUNCE = "PERMANENT_BOUNCE"


class BulkContactFailureReason(str, Enum):
    DUPLICATE_IN_REQUEST = "DUPLICATE_IN_REQUEST"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class _BaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Contact(_BaseModel):
    id: str
    email: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    status: SubscriptionStatus
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(alias="createdAt")


class Tag(_BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(alias="createdAt")


class BulkContactFailure(_BaseModel):
    index: int
    email: str
    reason: BulkContactFailureReason


class BulkContactResult(_BaseModel):
    failed: List[BulkContactFailure] = Field(default_factory=list)


class PaginatedContacts(_BaseModel):
    subscribers: List[Contact]
    total: int
    page: int
    limit: int


class PaginatedTags(_BaseModel):
    tags: List[Tag]
    total: int
    page: int
    limit: int


class _ContactEnvelope(_BaseModel):
    subscriber: Contact


class _TagEnvelope(_BaseModel):
    tag: Tag
