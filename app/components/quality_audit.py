import reflex as rx

from app.states.upload_state import CleaningStep, UploadState


def _metric(
    icon: str, label: str, value: rx.Var | str, tone: str, caption: str
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
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-0.5 truncate",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def audit_score_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Data quality score",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{UploadState.clean_rows} of {UploadState.raw_rows} rows from “{UploadState.source_label}” were kept for these metrics.",
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                f"{UploadState.quality_score}%",
                class_name="text-2xl font-semibold text-blue-600 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-2 rounded-full bg-blue-600 transition-all duration-500",
                style={"width": f"{UploadState.quality_score}%"},
            ),
            class_name="h-2 w-full rounded-full bg-gray-100 overflow-hidden mt-4",
        ),
        rx.el.p(
            "Score combines the share of rows we could keep with whether the required date and revenue columns are mapped.",
            class_name="text-xs font-medium text-gray-400 mt-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def audit_metric_grid() -> rx.Component:
    return rx.el.div(
        _metric(
            "rows-3",
            "Original rows",
            UploadState.raw_rows,
            "gray",
            "Rows below the header row",
        ),
        _metric(
            "list-checks",
            "Rows powering metrics",
            UploadState.clean_rows,
            "green",
            "After cleaning",
        ),
        _metric(
            "copy",
            "Duplicates removed",
            UploadState.removed_duplicates,
            "blue",
            "Identical rows collapsed",
        ),
        _metric(
            "eraser",
            "Blank rows removed",
            UploadState.removed_blank_rows,
            "blue",
            "Empty and spacer lines",
        ),
        _metric(
            "circle-slash",
            "Missing values",
            UploadState.missing_values,
            "amber",
            "Empty cells across all columns",
        ),
        _metric(
            "calendar-x",
            "Invalid dates",
            UploadState.invalid_dates,
            "amber",
            "In the mapped date column",
        ),
        _metric(
            "badge-dollar-sign",
            "Invalid revenue values",
            UploadState.invalid_revenue,
            "amber",
            "In the mapped revenue column",
        ),
        _metric(
            "columns-3",
            "Columns detected",
            UploadState.columns.length(),
            "blue",
            "Including derived columns",
        ),
        class_name="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full",
    )


def _detected_row(item: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "circle-check", class_name="h-4 w-4 text-green-600 shrink-0 mt-0.5"
        ),
        rx.el.div(
            rx.el.p(
                item["role"], class_name="text-sm font-semibold text-gray-900"
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


def mapping_audit_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "wand-sparkles", class_name="h-4 w-4 text-green-600"
                    ),
                    rx.el.p(
                        "Columns feeding these metrics",
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
                        "No column was auto-matched — the mapping you chose on the upload page is being used.",
                        class_name="text-sm font-medium text-gray-500",
                    ),
                ),
                class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
            ),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("hand", class_name="h-4 w-4 text-yellow-600"),
                    rx.el.p(
                        "Still needs manual mapping",
                        class_name="text-sm font-semibold text-gray-900",
                    ),
                    class_name="flex items-center gap-2 mb-3",
                ),
                rx.cond(
                    UploadState.needs_manual_mapping.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            UploadState.needs_manual_mapping, _pending_row
                        ),
                        class_name="flex flex-col gap-2",
                    ),
                    rx.el.div(
                        rx.icon(
                            "circle-check", class_name="h-4 w-4 text-green-600"
                        ),
                        rx.el.p(
                            "Every field is mapped — nothing is missing from the metrics.",
                            class_name="text-sm font-medium text-gray-600",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                ),
                rx.el.a(
                    rx.icon("columns-3", class_name="h-4 w-4"),
                    "Change column mapping",
                    href="/",
                    class_name="flex items-center gap-2 w-fit rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors mt-4",
                ),
                class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
            ),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        class_name="flex flex-col lg:flex-row gap-4 w-full",
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


def derived_audit_card() -> rx.Component:
    return rx.cond(
        UploadState.derived_fields.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.icon("wand-sparkles", class_name="h-4 w-4 text-indigo-600"),
                rx.el.p(
                    "Derived columns used in these metrics",
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
            class_name="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-5 w-full",
        ),
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


def cleaning_audit_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "What was changed before charting",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Every transformation applied to your file, in plain English.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-2",
        ),
        rx.el.div(
            rx.foreach(UploadState.cleaning_log, _log_row),
            class_name="divide-y divide-gray-100",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _chip(name: rx.Var) -> rx.Component:
    return rx.el.span(
        name,
        class_name="w-fit rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600",
    )


def unused_columns_card() -> rx.Component:
    return rx.cond(
        UploadState.unmapped_columns.length() > 0,
        rx.el.div(
            rx.el.p(
                "Columns kept but not used in any metric",
                class_name="text-sm font-semibold text-gray-900",
            ),
            rx.el.p(
                "Map one of these on the upload page if it should feed the dashboard.",
                class_name="text-xs font-medium text-gray-500 mt-0.5",
            ),
            rx.el.div(
                rx.foreach(UploadState.unmapped_columns, _chip),
                class_name="flex flex-wrap gap-2 mt-3",
            ),
            class_name="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm w-full",
        ),
    )


def privacy_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("lock", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"),
            rx.el.div(
                rx.el.p(
                    "Privacy",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Your spreadsheet is parsed in memory on this server for your session only. Nothing is stored on disk, shared, or sent to a third-party service, and this audit is generated fresh from the same cleaned rows the charts use.",
                    class_name="text-sm font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-2",
        ),
        class_name="rounded-2xl border border-gray-200 bg-gray-50 p-5 w-full",
    )


def _audit_body() -> rx.Component:
    return rx.el.div(
        audit_score_card(),
        audit_metric_grid(),
        derived_audit_card(),
        mapping_audit_row(),
        cleaning_audit_card(),
        unused_columns_card(),
        privacy_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def audit_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("shield-check", class_name="h-6 w-6 text-blue-600"),
            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-blue-50 mb-4",
        ),
        rx.el.h2(
            "No audit to show yet",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.p(
            "Upload a spreadsheet and this tab will explain exactly which rows and columns produced the numbers on the dashboard.",
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("cloud-upload", class_name="h-4 w-4"),
                "Go to upload",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors",
            ),
            rx.el.a(
                rx.icon("shield-check", class_name="h-4 w-4"),
                "Full data quality page",
                href="/data-quality",
                class_name="flex items-center gap-2 w-fit rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-100 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-center gap-3 mt-5",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white px-6 py-16 shadow-sm w-full",
    )


def quality_audit_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("shield-check", class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Data quality audit",
                    class_name="text-xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "How trustworthy the numbers on this dashboard are, and exactly what we changed to get them.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(UploadState.has_data, _audit_body(), audit_unavailable()),
        class_name="flex flex-col gap-6 w-full",
    )
