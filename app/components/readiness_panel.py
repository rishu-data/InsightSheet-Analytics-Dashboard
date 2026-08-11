import reflex as rx

from app.states.upload_state import CleaningStep, UploadState


def _status_badge() -> rx.Component:
    return rx.match(
        UploadState.readiness,
        (
            "ready",
            rx.el.span(
                rx.icon("circle-check", class_name="h-3.5 w-3.5"),
                "Ready",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
            ),
        ),
        (
            "needs_mapping",
            rx.el.span(
                rx.icon("circle-alert", class_name="h-3.5 w-3.5"),
                "Needs review",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
            ),
        ),
        rx.el.span(
            rx.icon("clock", class_name="h-3.5 w-3.5"),
            "Waiting",
            class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-500",
        ),
    )


def _stat(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(value, class_name="text-2xl font-semibold text-gray-900 mt-2"),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def readiness_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    UploadState.readiness_title,
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    UploadState.readiness_detail,
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Data quality",
                    class_name="text-xs font-medium text-gray-500",
                ),
                rx.el.span(
                    f"{UploadState.quality_score}%",
                    class_name="text-xs font-semibold text-blue-600",
                ),
                class_name="flex items-center justify-between mb-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-2 rounded-full bg-blue-600 transition-all duration-500",
                    style={"width": f"{UploadState.quality_score}%"},
                ),
                class_name="h-2 w-full rounded-full bg-gray-100 overflow-hidden",
            ),
            class_name="mt-5",
        ),
        rx.el.div(
            _stat("Rows read", UploadState.raw_rows, "rows-3"),
            _stat("Clean rows", UploadState.clean_rows, "list-checks"),
            _stat("Columns", UploadState.columns.length(), "columns-3"),
            _stat("Dates fixed", UploadState.parsed_dates, "calendar-check"),
            class_name="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )


def _log_row(step: CleaningStep) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(step["icon"], class_name="h-4 w-4"),
            class_name=rx.match(
                step["tone"],
                (
                    "green",
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-green-100 text-green-600 shrink-0",
                ),
                (
                    "amber",
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-yellow-100 text-yellow-600 shrink-0",
                ),
                "flex items-center justify-center h-8 w-8 rounded-lg bg-blue-100 text-blue-600 shrink-0",
            ),
        ),
        rx.el.div(
            rx.el.p(
                step["title"], class_name="text-sm font-semibold text-gray-900"
            ),
            rx.el.p(
                step["detail"], class_name="text-sm font-medium text-gray-500"
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 py-3",
    )


def cleaning_log_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "What we cleaned",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Every change we made to your file, in plain English.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-2",
        ),
        rx.el.div(
            rx.foreach(UploadState.cleaning_log, _log_row),
            class_name="divide-y divide-gray-100",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )
