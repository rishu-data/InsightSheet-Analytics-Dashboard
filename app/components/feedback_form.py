import reflex as rx

from app.states.feedback_state import CATEGORIES, FeedbackState, FeedbackEntry

_STAR_ACTIVE = "flex items-center justify-center h-11 w-11 rounded-xl border border-blue-200 bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
_STAR_IDLE = "flex items-center justify-center h-11 w-11 rounded-xl border border-gray-200 bg-white text-gray-300 hover:border-blue-300 hover:text-blue-400 transition-colors"


def _star_button(value: int) -> rx.Component:
    return rx.el.button(
        rx.icon("star", class_name="h-5 w-5"),
        type="button",
        aria_label=f"Rate {value} out of 5",
        on_click=lambda: FeedbackState.select_rating(value),
        class_name=rx.cond(
            FeedbackState.rating >= value, _STAR_ACTIVE, _STAR_IDLE
        ),
    )


def _rating_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("star", class_name="h-3.5 w-3.5 text-blue-600"),
                rx.el.span(
                    "Your rating",
                    class_name="text-xs font-semibold text-gray-600",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                FeedbackState.rating_display,
                class_name=rx.cond(
                    FeedbackState.has_rating,
                    "w-fit rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600",
                    "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-2",
        ),
        rx.el.div(
            _star_button(1),
            _star_button(2),
            _star_button(3),
            _star_button(4),
            _star_button(5),
            class_name="flex items-center gap-2 mt-2.5",
        ),
        rx.el.p(
            FeedbackState.rating_label,
            class_name=rx.cond(
                FeedbackState.has_rating,
                "text-sm font-semibold text-gray-900 mt-2",
                "text-sm font-medium text-gray-500 mt-2",
            ),
        ),
        class_name="w-full",
    )


def _category_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("tags", class_name="h-3.5 w-3.5 text-blue-600"),
            rx.el.span(
                "Category", class_name="text-xs font-semibold text-gray-600"
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    CATEGORIES,
                    lambda option: rx.el.option(option, value=option),
                ),
                name="category",
                value=FeedbackState.category,
                on_change=FeedbackState.select_category,
                class_name="w-full appearance-none rounded-xl border border-gray-300 bg-white px-4 py-2.5 pr-10 text-sm font-medium text-gray-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-hidden transition-colors cursor-pointer",
            ),
            rx.icon(
                "chevron-down",
                class_name="h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        rx.el.p(
            "Pick the part of InsightSheet your feedback is about.",
            class_name="text-xs font-medium text-gray-500 mt-1.5",
        ),
        class_name="w-full",
    )


def _message_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "message-square", class_name="h-3.5 w-3.5 text-blue-600"
                ),
                rx.el.span(
                    "Your feedback",
                    class_name="text-xs font-semibold text-gray-600",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                f"{FeedbackState.character_count} characters",
                class_name="text-xs font-medium text-gray-400",
            ),
            class_name="flex flex-wrap items-center justify-between gap-2",
        ),
        rx.el.textarea(
            name="message",
            placeholder="Tell us what you liked or what we can improve...",
            rows="6",
            default_value=FeedbackState.message,
            on_change=FeedbackState.set_message.debounce(300),
            class_name="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-hidden transition-colors resize-y mt-1.5",
        ),
        class_name="w-full",
    )


def _validation_banner() -> rx.Component:
    return rx.cond(
        FeedbackState.error_message != "",
        rx.el.div(
            rx.icon(
                "triangle-alert",
                class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
            ),
            rx.el.p(
                FeedbackState.error_message,
                class_name="text-sm font-medium text-yellow-700",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3",
        ),
    )


def _success_banner() -> rx.Component:
    return rx.cond(
        FeedbackState.success_message != "",
        rx.el.div(
            rx.icon(
                "circle-check",
                class_name="h-4 w-4 text-green-600 shrink-0 mt-0.5",
            ),
            rx.el.p(
                FeedbackState.success_message,
                class_name="text-sm font-semibold text-green-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-green-200 bg-green-100 px-4 py-3",
        ),
    )


def feedback_form_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "message-square-heart",
                        class_name="h-5 w-5 text-blue-600",
                    ),
                    class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-blue-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Share Your Feedback",
                        class_name="text-2xl font-semibold tracking-tight text-gray-900",
                    ),
                    rx.el.p(
                        "Help us improve InsightSheet by sharing your experience.",
                        class_name="text-sm font-medium text-gray-500 mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.span(
                rx.icon("lock", class_name="h-3.5 w-3.5"),
                "Kept in this session only",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        _success_banner(),
        _validation_banner(),
        rx.el.form(
            _rating_field(),
            _category_field(),
            _message_field(),
            rx.el.div(
                rx.el.p(
                    rx.cond(
                        FeedbackState.can_submit,
                        "Ready to send — thank you for taking the time.",
                        "A star rating and a short note are both required.",
                    ),
                    class_name="text-sm font-medium text-gray-500",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("eraser", class_name="h-4 w-4"),
                        "Clear",
                        type="button",
                        on_click=FeedbackState.clear_form,
                        class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
                    ),
                    rx.el.button(
                        rx.icon("send", class_name="h-4 w-4"),
                        "Submit Feedback",
                        type="submit",
                        disabled=FeedbackState.is_submitting,
                        class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors",
                    ),
                    class_name="flex flex-wrap items-center gap-3 shrink-0",
                ),
                class_name="flex flex-wrap items-center justify-between gap-3 pt-5 border-t border-gray-100",
            ),
            on_submit=FeedbackState.submit_feedback,
            class_name="flex flex-col gap-5 w-full",
        ),
        class_name="flex flex-col gap-5 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _entry_card(entry: FeedbackEntry) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("star", class_name="h-3.5 w-3.5 text-blue-600"),
                rx.el.span(
                    f"{entry['rating']} of 5",
                    class_name="text-xs font-semibold text-blue-600",
                ),
                class_name="flex items-center gap-1.5 w-fit rounded-md bg-blue-50 px-2 py-0.5",
            ),
            rx.el.span(
                entry["category"],
                class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600",
            ),
            rx.el.span(
                entry["submitted_at"],
                class_name="text-xs font-medium text-gray-400",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.p(
            entry["message"],
            class_name="text-sm font-medium text-gray-700 mt-3",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def feedback_history_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Feedback from this session",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Stored in memory so it can be connected to a backend later — nothing is saved to disk.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("list-checks", class_name="h-3.5 w-3.5"),
                    f"{FeedbackState.submission_count} submitted",
                    class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
                ),
                rx.el.span(
                    rx.icon("star", class_name="h-3.5 w-3.5"),
                    f"Average {FeedbackState.average_rating_display}",
                    class_name="flex items-center gap-1.5 w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700",
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.cond(
            FeedbackState.has_entries,
            rx.el.div(
                rx.foreach(FeedbackState.entries, _entry_card),
                class_name="flex flex-col gap-3",
            ),
            rx.el.div(
                rx.icon("inbox", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "Nothing submitted yet — your feedback will appear here after you send it.",
                    class_name="text-sm font-medium text-gray-500 max-w-md text-center",
                ),
                class_name="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 px-6 py-12",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def feedback_info_card() -> rx.Component:
    return rx.el.div(
        rx.icon("info", class_name="h-4 w-4 text-blue-600 shrink-0 mt-0.5"),
        rx.el.p(
            "Feedback is kept for this session only and is never attached to your uploaded "
            "spreadsheet. It helps us decide which part of InsightSheet to improve next.",
            class_name="text-sm font-medium text-gray-600",
        ),
        class_name="flex items-start gap-2 rounded-2xl border border-blue-100 bg-blue-50/50 p-4 w-full",
    )
