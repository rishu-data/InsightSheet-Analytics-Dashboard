"""Lightweight self-checks for the Razorpay webhook logic.

Run with:  python -m app.tests_razorpay_webhook

Only pure helpers are exercised (signature verification, event mapping,
identifier resolution, metadata safety). No database or network is touched and
no secret value is ever printed.
"""

import hashlib
import hmac
import json

from app.models import SubscriptionStatus
from app.razorpay_webhook import (
    _fallback_event_id,
    _target_status,
    resolve_user_identifier,
    safe_metadata,
    verify_signature,
)

SECRET = "test_secret_value"


def _sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_signature() -> None:
    body = json.dumps({"event": "payment.captured"}).encode()
    assert verify_signature(body, _sign(body), SECRET)
    assert verify_signature(body, _sign(body).upper(), SECRET)
    assert not verify_signature(body, "deadbeef", SECRET)
    assert not verify_signature(body, _sign(body), "other_secret")
    assert not verify_signature(body, "", SECRET)
    assert not verify_signature(b"", _sign(b""), SECRET)
    assert not verify_signature(body + b" ", _sign(body), SECRET)


def test_event_mapping() -> None:
    for name in (
        "subscription.activated",
        "subscription.charged",
        "payment.captured",
    ):
        assert _target_status(name, None) is SubscriptionStatus.ACTIVE
    for name in (
        "subscription.authenticated",
        "subscription.pending",
        "payment.authorized",
    ):
        assert _target_status(name, None) is SubscriptionStatus.PENDING
        assert (
            _target_status(name, SubscriptionStatus.FREE)
            is SubscriptionStatus.PENDING
        )
        # A stronger status is never downgraded to PENDING.
        for stronger in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
            SubscriptionStatus.PAYMENT_FAILED,
        ):
            assert _target_status(name, stronger) is None
    assert (
        _target_status("payment.failed", None)
        is SubscriptionStatus.PAYMENT_FAILED
    )
    assert (
        _target_status("subscription.halted", None)
        is SubscriptionStatus.PAYMENT_FAILED
    )
    assert (
        _target_status("subscription.cancelled", None)
        is SubscriptionStatus.CANCELLED
    )
    assert (
        _target_status("subscription.completed", None)
        is SubscriptionStatus.EXPIRED
    )
    assert (
        _target_status("subscription.expired", None)
        is SubscriptionStatus.EXPIRED
    )
    assert _target_status("order.paid", None) is None


def test_identifier_priority() -> None:
    notes = {
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_1",
                    "notes": {"user_id": "user-42"},
                    "customer_id": "cust_1",
                }
            }
        }
    }
    assert resolve_user_identifier(notes["payload"]) == "user-42"

    email = {
        "subscription": {
            "entity": {"id": "sub_2", "customer_email": "buyer@example.com"}
        }
    }
    assert resolve_user_identifier(email) == "buyer@example.com"

    contact = {
        "payment": {"entity": {"id": "pay_1", "contact": "+910000000000"}}
    }
    assert resolve_user_identifier(contact) == "+910000000000"

    customer = {
        "subscription": {"entity": {"id": "sub_3", "customer_id": "cust_9"}}
    }
    assert resolve_user_identifier(customer) == "cust_9"

    only_sub = {"subscription": {"entity": {"id": "sub_4"}}}
    assert resolve_user_identifier(only_sub) == "sub_4"

    assert resolve_user_identifier({}) == ""


def test_metadata_is_safe() -> None:
    payload = {
        "subscription": {"entity": {"id": "sub_5", "plan_id": "plan_1"}},
        "payment": {
            "entity": {
                "id": "pay_5",
                "amount": 19900,
                "currency": "INR",
                "method": "card",
                "card": {"number": "4111111111111111", "cvv": "123"},
                "token": "tok_secret",
            }
        },
    }
    text = safe_metadata("subscription.charged", payload)
    data = json.loads(text)
    assert data["subscription_id"] == "sub_5"
    assert data["payment_id"] == "pay_5"
    assert data["amount_minor_units"] == 19900
    assert "4111111111111111" not in text
    assert "cvv" not in text
    assert "token" not in text


def test_fallback_event_id() -> None:
    body = b'{"event":"payment.captured"}'
    first = _fallback_event_id(body)
    assert first == _fallback_event_id(body)
    assert first != _fallback_event_id(body + b" ")
    assert len(first) <= 128


def main() -> None:
    test_signature()
    test_event_mapping()
    test_identifier_priority()
    test_metadata_is_safe()
    test_fallback_event_id()
    print("All Razorpay webhook self-checks passed.")


if __name__ == "__main__":
    main()
