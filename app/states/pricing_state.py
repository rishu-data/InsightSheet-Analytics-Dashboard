"""Pricing / Upgrade state.

The Pro checkout destination is read from the INSIGHTSHEET_PAYMENT_URL
environment variable on the server side only. No key, secret or credential is
stored in the app, and no payment success state is ever faked — if the variable
is missing or blank we simply tell the visitor that setup is in progress.
"""

import logging
import os

import reflex as rx

PAYMENT_ENV_VAR = "INSIGHTSHEET_PAYMENT_URL"
PAYMENT_UNAVAILABLE = (
    "Payment setup is currently being configured. Please try again later."
)

FREE_FEATURES: list[str] = [
    "CSV / Excel upload",
    "Basic KPIs",
    "Basic dashboard",
    "Basic analytics",
    "Basic data-quality checks",
    "Limited reports",
]

PRO_FEATURES: list[str] = [
    "Advanced analytics",
    "RFM customer segmentation",
    "Sales forecasting",
    "Profitability analytics",
    "AI-powered insights",
    "Ask AI support",
    "PDF reports",
    "Excel reports",
    "Advanced dashboard analysis",
    "Higher usage limits",
]

PRO_BUTTON_LABEL = "Upgrade to Pro \u2014 \u20b9199/month"

FAQ_ITEMS: list[tuple[str, str, str]] = [
    (
        "shield-check",
        "Is my spreadsheet stored anywhere?",
        "No. On both plans your file is parsed in memory for your session only — "
        "nothing is written to disk, shared, or sent to a third-party service.",
    ),
    (
        "credit-card",
        "How is payment handled?",
        "Checkout happens entirely on an external, configured payment page. "
        "InsightSheet never collects or stores card details or credentials.",
    ),
    (
        "rotate-ccw",
        "Can I start on Free and upgrade later?",
        "Yes. Start Free needs no payment details at all, and you can move to Pro "
        "whenever you need forecasting, RFM segmentation or AI insights.",
    ),
]


class PricingState(rx.State):
    """Holds the Pro checkout redirect result and any setup message."""

    notice: str = ""
    is_redirecting: bool = False

    @rx.var
    def has_notice(self) -> bool:
        return bool(self.notice)

    @rx.event
    def start_free(self):
        """Free plan requires no payment — go straight to the upload workflow."""
        self.notice = ""
        return rx.redirect("/")

    @rx.event
    def upgrade_to_pro(self):
        """Open the configured external checkout page, if one is configured."""
        self.notice = ""
        self.is_redirecting = True
        yield
        try:
            checkout_url = str(
                os.environ.get(PAYMENT_ENV_VAR, "") or ""
            ).strip()
        except Exception as e:
            logging.exception(f"Error reading {PAYMENT_ENV_VAR}: {e}")
            checkout_url = ""
        self.is_redirecting = False
        if not checkout_url:
            self.notice = PAYMENT_UNAVAILABLE
            return
        yield rx.redirect(checkout_url, is_external=True)

    @rx.event
    def dismiss_notice(self):
        self.notice = ""
