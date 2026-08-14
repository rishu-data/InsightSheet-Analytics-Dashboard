import reflex as rx

from app.components.feedback_form import (
    feedback_form_card,
    feedback_history_card,
    feedback_info_card,
)
from app.components.sidebar import page_shell


def _feedback_body() -> rx.Component:
    return rx.el.div(
        feedback_form_card(),
        feedback_info_card(),
        feedback_history_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def feedback_page() -> rx.Component:
    return page_shell(
        "feedback",
        "Share Your Feedback",
        "Help us improve InsightSheet by sharing your experience.",
        _feedback_body(),
    )
