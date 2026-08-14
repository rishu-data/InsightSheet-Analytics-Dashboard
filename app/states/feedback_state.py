"""Lightweight, in-session feedback capture.

Submissions are held in state only (a simple list of records) so a persistence
backend can be connected later without touching the UI. No database, auth or
external service is involved.
"""

import logging
from datetime import datetime
from typing import TypedDict

import reflex as rx

CATEGORIES: list[str] = [
    "Overall Experience",
    "Dashboard",
    "Analytics",
    "AI Insights",
    "RFM Analysis",
    "Forecasting",
    "Reports & Exports",
    "Data Upload",
    "Other",
]

DEFAULT_CATEGORY = "Overall Experience"
SUCCESS_MESSAGE = "Thank you for your feedback! \u2b50"

RATING_LABELS: dict[int, str] = {
    0: "No rating selected yet",
    1: "Poor",
    2: "Fair",
    3: "Good",
    4: "Very good",
    5: "Excellent",
}


class FeedbackEntry(TypedDict):
    id: str
    rating: int
    category: str
    message: str
    submitted_at: str


class FeedbackState(rx.State):
    """Holds the feedback form and the submissions made this session."""

    rating: int = 0
    category: str = DEFAULT_CATEGORY
    message: str = ""

    error_message: str = ""
    success_message: str = ""
    is_submitting: bool = False
    form_key: int = 0

    entries: list[FeedbackEntry] = []

    @rx.var
    def has_rating(self) -> bool:
        return 1 <= self.rating <= 5

    @rx.var
    def rating_label(self) -> str:
        return RATING_LABELS.get(self.rating, RATING_LABELS[0])

    @rx.var
    def rating_display(self) -> str:
        if not self.has_rating:
            return "Not rated"
        return f"{self.rating} of 5"

    @rx.var
    def character_count(self) -> int:
        return len(self.message.strip())

    @rx.var
    def can_submit(self) -> bool:
        return self.has_rating and bool(self.message.strip())

    @rx.var
    def submission_count(self) -> int:
        return len(self.entries)

    @rx.var
    def has_entries(self) -> bool:
        return len(self.entries) > 0

    @rx.var
    def average_rating_display(self) -> str:
        if not self.entries:
            return "\u2014"
        total = sum(int(entry["rating"]) for entry in self.entries)
        return f"{total / len(self.entries):.1f} / 5"

    @rx.event
    def select_rating(self, value: int):
        try:
            rating = int(value)
        except (TypeError, ValueError):
            rating = 0
        self.rating = rating if 1 <= rating <= 5 else 0
        self.error_message = ""
        self.success_message = ""

    @rx.event
    def select_category(self, value: str):
        choice = str(value or "")
        self.category = choice if choice in CATEGORIES else DEFAULT_CATEGORY
        self.success_message = ""

    @rx.event
    def set_message(self, value: str):
        self.message = str(value or "")
        if self.message.strip():
            self.error_message = ""
        self.success_message = ""

    @rx.event
    def clear_form(self):
        self._reset_form()
        self.error_message = ""
        self.success_message = ""

    def _reset_form(self) -> None:
        self.rating = 0
        self.category = DEFAULT_CATEGORY
        self.message = ""
        self.form_key += 1

    @rx.event
    def submit_feedback(self, form_data: dict):
        """Validate, store in session state, then reset the form."""
        typed = str(form_data.get("message", "") or "")
        text = (typed if typed.strip() else self.message).strip()
        self.success_message = ""
        if not self.has_rating and not text:
            self.error_message = (
                "Please choose a star rating and tell us what you think "
                "before submitting."
            )
            return
        if not self.has_rating:
            self.error_message = (
                "Please choose a star rating from 1 to 5 before submitting."
            )
            return
        if not text:
            self.error_message = (
                "Please write a short note about your experience before "
                "submitting — empty feedback can't be sent."
            )
            return
        self.error_message = ""
        self.is_submitting = True
        try:
            entry = FeedbackEntry(
                id=f"feedback-{len(self.entries) + 1}",
                rating=int(self.rating),
                category=self.category
                if self.category in CATEGORIES
                else DEFAULT_CATEGORY,
                message=text,
                submitted_at=datetime.now().strftime("%b %d, %Y at %H:%M"),
            )
            self.entries.insert(0, entry)
            self._reset_form()
            self.success_message = SUCCESS_MESSAGE
        except Exception as e:
            logging.exception(f"Error storing feedback: {e}")
            self.error_message = (
                "Something went wrong saving that feedback. Please try again."
            )
        finally:
            self.is_submitting = False
