import reflex as rx

from app.states.upload_state import UploadState


def _metric(
    icon: str, label: str, value: rx.Var | str, tone: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                icon,
                class_name={
                    "blue": "h-4 w-4 text-blue-600",
                    "green": "h-4 w-4 text-green-600",
                    "amber": "h-4 w-4 text-yellow-600",
                    "gray": "h-4 w-4 text-gray-400",
                }[tone],
            ),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(value, class_name="text-2xl font-semibold text-gray-900 mt-2"),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def _detected_row(item: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.icon("circle-check", class_name="h-4 w-4 text-green-600 shrink-0"),
        rx.el.div(
            rx.el.p(
                item["role"],
                class_name="text-sm font-semibold text-gray-900",
            ),
            rx.el.p(
                f"matched to “{item['column']}”",
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 rounded-xl border border-gray-100 bg-gray-50/70 p-3",
    )


def _pending_row(item: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "circle-dashed", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["role"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    item["requirement"],
                    class_name=rx.cond(
                        item["requirement"] == "Required",
                        "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
                        "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
                    ),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                item["detail"],
                class_name="text-xs font-medium text-gray-500 mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 rounded-xl border border-gray-100 bg-gray-50/70 p-3",
    )


def _derived_row(field: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.icon(
            field["icon"], class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    field["name"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    f"Used as {field['role']}",
                    class_name="w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                field["detail"],
                class_name="text-xs font-medium text-gray-500 mt-0.5",
            ),
            rx.el.p(
                f"{field['formula']} · built from {field['sources']} · {field['filled']} of rows filled",
                class_name="text-xs font-medium text-indigo-500 mt-1",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 rounded-xl border border-indigo-100 bg-white p-3",
    )


def _derived_block() -> rx.Component:
    return rx.cond(
        UploadState.derived_fields.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.icon("wand-sparkles", class_name="h-4 w-4 text-indigo-600"),
                rx.el.p(
                    "Derived columns",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                class_name="flex items-center gap-2 mb-3",
            ),
            rx.el.div(
                rx.foreach(UploadState.derived_fields, _derived_row),
                class_name="flex flex-col gap-2",
            ),
            rx.el.p(
                "Derived columns are calculated from values already in your file — nothing is invented or estimated.",
                class_name="text-xs font-medium text-gray-500 mt-3",
            ),
            class_name="w-full rounded-2xl border border-indigo-200 bg-indigo-50/50 p-5 mt-4",
        ),
    )


def _chip(name: rx.Var) -> rx.Component:
    return rx.el.span(
        name,
        class_name="w-fit rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600",
    )


def _detected_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("wand-sparkles", class_name="h-4 w-4 text-green-600"),
            rx.el.p(
                "Auto-detected columns",
                class_name="text-sm font-semibold text-gray-900",
            ),
            class_name="flex items-center gap-2 mb-3",
        ),
        rx.cond(
            UploadState.auto_detected.length() > 0,
            rx.el.div(
                rx.foreach(UploadState.auto_detected, _detected_row),
                class_name="flex flex-col gap-2",
            ),
            rx.el.p(
                "We couldn't confidently match any column — map them manually above.",
                class_name="text-sm font-medium text-gray-500",
            ),
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5",
    )


def _pending_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("hand", class_name="h-4 w-4 text-yellow-600"),
            rx.el.p(
                "Columns needing manual mapping",
                class_name="text-sm font-semibold text-gray-900",
            ),
            class_name="flex items-center gap-2 mb-3",
        ),
        rx.cond(
            UploadState.needs_manual_mapping.length() > 0,
            rx.el.div(
                rx.foreach(UploadState.needs_manual_mapping, _pending_row),
                class_name="flex flex-col gap-2",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-4 w-4 text-green-600"),
                rx.el.p(
                    "Every field is mapped. Nothing left to do here.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                class_name="flex items-center gap-2",
            ),
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5",
    )


def _report_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _metric("rows-3", "Original rows", UploadState.raw_rows, "gray"),
            _metric(
                "list-checks", "Cleaned rows", UploadState.clean_rows, "green"
            ),
            _metric(
                "copy",
                "Duplicates removed",
                UploadState.removed_duplicates,
                "blue",
            ),
            _metric(
                "eraser",
                "Blank rows removed",
                UploadState.removed_blank_rows,
                "blue",
            ),
            _metric(
                "circle-slash",
                "Missing values",
                UploadState.missing_values,
                "amber",
            ),
            _metric(
                "calendar-x",
                "Invalid dates",
                UploadState.invalid_dates,
                "amber",
            ),
            _metric(
                "badge-dollar-sign",
                "Invalid revenue values",
                UploadState.invalid_revenue,
                "amber",
            ),
            _metric(
                "columns-3",
                "Columns detected",
                UploadState.columns.length(),
                "blue",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-4",
        ),
        _derived_block(),
        rx.el.div(
            rx.el.div(_detected_block(), class_name="w-full lg:flex-1 min-w-0"),
            rx.el.div(_pending_block(), class_name="w-full lg:flex-1 min-w-0"),
            class_name="flex flex-col lg:flex-row gap-4 mt-4",
        ),
        rx.cond(
            UploadState.unmapped_columns.length() > 0,
            rx.el.div(
                rx.el.p(
                    "Columns we kept but aren't using in metrics",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.div(
                    rx.foreach(UploadState.unmapped_columns, _chip),
                    class_name="flex flex-wrap gap-2 mt-2",
                ),
                class_name="rounded-2xl border border-gray-200 bg-white p-5 mt-4",
            ),
        ),
        rx.el.div(
            rx.icon("lock", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"),
            rx.el.p(
                "This report is generated in memory for your session only. Your file is never stored, shared or sent to a third party.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-4",
        ),
        class_name="mt-5 w-full",
    )


def quality_report() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.el.div(
                    rx.icon("shield-check", class_name="h-4 w-4 text-blue-600"),
                    class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.p(
                        "Data quality report",
                        class_name="text-lg font-semibold text-gray-900 text-left",
                    ),
                    rx.el.p(
                        f"{UploadState.clean_rows} of {UploadState.raw_rows} rows kept · quality score {UploadState.quality_score}%",
                        class_name="text-sm font-medium text-gray-500 text-left",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    rx.cond(
                        UploadState.report_open, "Hide details", "Show details"
                    ),
                    class_name="hidden sm:inline text-xs font-semibold text-blue-700",
                ),
                rx.icon(
                    rx.cond(
                        UploadState.report_open, "chevron-up", "chevron-down"
                    ),
                    class_name="h-4 w-4 text-gray-500",
                ),
                class_name="flex items-center gap-2 shrink-0",
            ),
            on_click=UploadState.toggle_report,
            class_name="flex w-full items-center justify-between gap-4 text-left",
        ),
        rx.cond(UploadState.report_open, _report_body()),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )
