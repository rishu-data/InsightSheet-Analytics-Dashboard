"""Persistent database models for Razorpay subscription state.

Only non-sensitive billing metadata is stored here. Card numbers, CVV, UPI PIN,
banking passwords, API keys, webhook secrets and signatures are never persisted.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    """Single declarative base shared by every model in this app."""


class SubscriptionStatus(enum.StrEnum):
    """Lifecycle of a Razorpay subscription as reflected by verified webhooks."""

    FREE = "FREE"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Subscription(Base):
    """Current subscription state for a single user identifier.

    `user_identifier` is an app-level identifier (for example an email or an
    opaque session/account id) — never a payment credential.
    """

    __tablename__ = "razorpay_subscription"
    __table_args__ = (
        Index("ix_razorpay_subscription_status", "status"),
        Index(
            "ix_razorpay_subscription_subscription_id",
            "razorpay_subscription_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_identifier: Mapped[str] = mapped_column(
        String(320), unique=True, index=True
    )

    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )
    razorpay_plan_id: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="razorpay_subscription_status",
            native_enum=False,
            validate_strings=True,
            length=32,
        ),
        default=SubscriptionStatus.FREE,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        init=False,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )


class WebhookEvent(Base):
    """One row per Razorpay webhook event id, used for idempotent processing.

    Stores only the event id, the event name, when it was processed and a short
    safe note (for example the subscription id it applied to). Raw payloads,
    signatures and secrets are never stored.
    """

    __tablename__ = "razorpay_webhook_event"
    __table_args__ = (Index("ix_razorpay_webhook_event_name", "event_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    razorpay_event_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True
    )
    event_name: Mapped[str] = mapped_column(String(128))

    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(64), default=None, nullable=True
    )

    resulting_status: Mapped[SubscriptionStatus | None] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="razorpay_webhook_event_status",
            native_enum=False,
            validate_strings=True,
            length=32,
        ),
        default=None,
        nullable=True,
    )

    safe_metadata: Mapped[str | None] = mapped_column(
        Text, default=None, nullable=True
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), init=False, server_default=func.now()
    )
