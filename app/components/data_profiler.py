import reflex as rx

from app.states.profiler import (
    BusinessColumn,
    CleaningOperation,
    ColumnProfile,
    ScorePart,
    TypeCount,
)
from app.states.upload_state import UploadState

_TONE_TEXT: dict[str, str] = {
    "good": "text-green-600",
    "info": "text-blue-600",
    "warn": "text-yellow-600",
    "bad": "text-red-500",
}


def _band_badge() -> rx.Component:
    return rx.el.span(
        rx.icon("gauge", class_name="h-3.5 w-3.5"),
        UploadState.quality_band,
        class_name=rx.match(
            UploadState.quality_band_tone,
            (
                "good",
                "flex items-center gap-1.5 w-fit rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
            ),
            (
                "info",
                "flex items-center gap-1.5 w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-600",
            ),
            (
                "warn",
                "flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
            ),
            "flex items-center gap-1.5 w-fit rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-500",
        ),
    )


def _score_part(part: ScorePart) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(part["icon"], class_name="h-3.5 w-3.5 text-blue-600"),
                rx.el.span(
                    part["label"],
                    class_name="text-xs font-semibold text-gray-900",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.span(
                f"{part['points']} / {part['max_points']}",
                class_name="text-xs font-semibold text-blue-600 shrink-0",
            ),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-full bg-blue-600 transition-all duration-500",
                style={"width": f"{part['pct']}%"},
            ),
            class_name="h-1.5 w-full rounded-full bg-gray-100 overflow-hidden mt-2.5",
        ),
        rx.el.p(
            part["detail"],
            class_name="text-xs font-medium text-gray-500 mt-2",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def profiler_score_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Data quality score",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    _band_badge(),
                    class_name="flex flex-wrap items-center gap-3",
                ),
                rx.el.p(
                    UploadState.quality_band_detail,
                    class_name="text-sm font-medium text-gray-500 mt-1 max-w-2xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    UploadState.quality_score.to_string(),
                    class_name="text-4xl font-semibold text-blue-600",
                ),
                rx.el.span(
                    "/ 100",
                    class_name="text-sm font-semibold text-gray-400 mb-1",
                ),
                class_name="flex items-end gap-1 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-4",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-2 rounded-full bg-blue-600 transition-all duration-500",
                style={"width": f"{UploadState.quality_score}%"},
            ),
            class_name="h-2 w-full rounded-full bg-gray-100 overflow-hidden mt-5",
        ),
        rx.el.div(
            rx.foreach(UploadState.score_breakdown, _score_part),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mt-5",
        ),
        rx.el.p(
            f"Scored from {UploadState.clean_rows} valid records across {UploadState.columns.length()} columns in “{UploadState.source_label}”.",
            class_name="text-xs font-medium text-gray-400 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _metric(
    icon: str, label: str, value: rx.Var | str, caption: rx.Var | str, tone: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name=f"h-4 w-4 {_TONE_TEXT[tone]}"),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-2xl font-semibold text-gray-900 mt-2 truncate",
        ),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-0.5 truncate",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def profiler_metric_grid() -> rx.Component:
    return rx.el.div(
        _metric(
            "database",
            "Dataset size",
            UploadState.dataset_size_display,
            f"{UploadState.total_cells} cells · {UploadState.file_size_kb} KB",
            "info",
        ),
        _metric(
            "columns-3",
            "Columns",
            UploadState.columns.length().to_string(),
            UploadState.column_type_caption,
            "info",
        ),
        _metric(
            "list-checks",
            "Valid records",
            UploadState.clean_rows.to_string(),
            f"{UploadState.raw_rows} rows read from the file",
            "good",
        ),
        _metric(
            "circle-slash",
            "Missing values",
            UploadState.missing_share_display,
            f"{UploadState.missing_cells} empty or unreadable cells",
            "warn",
        ),
        _metric(
            "copy",
            "Duplicate rows",
            UploadState.removed_duplicates.to_string(),
            "Identical rows collapsed into one",
            "info",
        ),
        _metric(
            "calendar-x",
            "Invalid dates",
            UploadState.invalid_date_cells.to_string(),
            f"Across {UploadState.date_columns} date column(s)",
            "warn",
        ),
        _metric(
            "badge-dollar-sign",
            "Invalid numbers",
            UploadState.invalid_number_cells.to_string(),
            f"Across {UploadState.numeric_columns} numeric column(s)",
            "warn",
        ),
        _metric(
            "scatter-chart",
            "Outliers",
            UploadState.outlier_cells.to_string(),
            "Numeric values beyond 1.5 × IQR",
            "bad",
        ),
        class_name="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full",
    )


def _type_chip(item: TypeCount) -> rx.Component:
    return rx.el.span(
        rx.icon(item["icon"], class_name="h-3.5 w-3.5 text-blue-600"),
        rx.el.span(item["label"], class_name="font-semibold text-gray-900"),
        rx.el.span(item["count"], class_name="text-blue-600 font-semibold"),
        class_name="flex items-center gap-2 w-fit rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium",
    )


def _business_row(item: BusinessColumn) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-4 w-4 text-blue-600"),
            class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["role"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    item["confidence"],
                    class_name=rx.cond(
                        item["confidence"] == "High",
                        "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
                        "w-fit rounded-md bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-600",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                f"“{item['column']}”",
                class_name="text-xs font-semibold text-gray-600 mt-0.5 truncate",
            ),
            rx.el.p(
                item["detail"],
                class_name="text-xs font-medium text-gray-500 mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/70 p-3",
    )


def business_columns_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Business columns detected",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{UploadState.business_columns.length()} of your columns were recognised as standard sales concepts.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.foreach(UploadState.type_summary, _type_chip),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.cond(
            UploadState.business_columns.length() > 0,
            rx.el.div(
                rx.foreach(UploadState.business_columns, _business_row),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3",
            ),
            rx.el.div(
                rx.icon("search-x", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "No column names matched a known business concept — use the mapping card to tell us what each column means.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-32 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _th(icon: str, label: str, right: bool) -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-gray-400"),
            rx.el.span(label),
            class_name=rx.cond(
                right,
                "flex items-center justify-end gap-2",
                "flex items-center gap-2",
            ),
        ),
        class_name="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap",
    )


def _count_cell(value: rx.Var, warn: rx.Var) -> rx.Component:
    return rx.el.td(
        rx.el.span(
            value,
            class_name=rx.cond(
                warn,
                "text-sm font-semibold text-yellow-600",
                "text-sm font-medium text-gray-700",
            ),
        ),
        class_name="px-4 py-3 whitespace-nowrap text-right",
    )


def _profile_row(col: ColumnProfile) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    col["name"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.cond(
                    col["role"] != "",
                    rx.el.span(
                        col["role"],
                        class_name="w-fit rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600",
                    ),
                ),
                class_name="flex flex-col items-start gap-1 min-w-0",
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.span(
                col["data_type"],
                class_name="w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-600",
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        col["missing_display"],
                        class_name=rx.match(
                            col["tone"],
                            ("good", "text-sm font-semibold text-green-600"),
                            ("info", "text-sm font-semibold text-blue-600"),
                            ("warn", "text-sm font-semibold text-yellow-600"),
                            "text-sm font-semibold text-red-500",
                        ),
                    ),
                    rx.el.span(
                        f"{col['missing']} cells",
                        class_name="text-xs font-medium text-gray-400",
                    ),
                    class_name="flex items-center justify-between gap-3",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name=rx.match(
                            col["tone"],
                            ("good", "h-1.5 rounded-full bg-green-500"),
                            ("info", "h-1.5 rounded-full bg-blue-500"),
                            ("warn", "h-1.5 rounded-full bg-yellow-500"),
                            "h-1.5 rounded-full bg-red-500",
                        ),
                        style={"width": f"{col['complete_pct']}%"},
                    ),
                    class_name="h-1.5 w-full min-w-[120px] rounded-full bg-gray-100 overflow-hidden mt-1.5",
                ),
                class_name="min-w-[140px]",
            ),
            class_name="px-4 py-3",
        ),
        rx.el.td(
            col["filled"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            col["unique"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        _count_cell(col["invalid"], col["invalid"] > 0),
        _count_cell(col["outliers"], col["outliers"] > 0),
        rx.el.td(
            col["sample"],
            class_name="px-4 py-3 text-sm font-medium text-gray-500 whitespace-nowrap max-w-[240px] truncate",
        ),
        class_name="hover:bg-blue-50/40 even:bg-gray-50/60 transition-colors",
    )


def column_profile_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Column-by-column profile",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Detected type, completeness, distinct values, invalid entries and outliers for every column we kept.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            _th("table", "Column", False),
                            _th("shapes", "Detected type", False),
                            _th("circle-slash", "Missing", False),
                            _th("list-checks", "Filled", True),
                            _th("fingerprint", "Unique", True),
                            _th("triangle-alert", "Invalid", True),
                            _th("scatter-chart", "Outliers", True),
                            _th("eye", "Sample", False),
                        ),
                        class_name="bg-gray-50 border-b border-gray-200",
                    ),
                    rx.el.tbody(
                        rx.foreach(UploadState.column_profiles, _profile_row),
                        class_name="divide-y divide-gray-100",
                    ),
                    class_name="table-auto min-w-full",
                ),
                class_name="overflow-x-auto",
            ),
            class_name="rounded-xl border border-gray-200 overflow-hidden",
        ),
        rx.el.p(
            "Outliers use the interquartile range (below Q1 − 1.5 × IQR or above Q3 + 1.5 × IQR) and are kept in the data — they are flagged, never removed.",
            class_name="text-xs font-medium text-gray-400 mt-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _operation_row(op: CleaningOperation) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(op["icon"], class_name="h-4 w-4"),
            class_name=rx.cond(
                op["applied"],
                "flex items-center justify-center h-8 w-8 rounded-lg bg-blue-100 text-blue-600 shrink-0",
                "flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 text-gray-400 shrink-0",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    op["title"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    op["count"],
                    class_name=rx.cond(
                        op["applied"],
                        "w-fit rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600",
                        "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                op["detail"],
                class_name="text-sm font-medium text-gray-500 mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/70 p-3",
    )


def cleaning_operations_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Cleaning operations performed",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{UploadState.operations_applied} of {UploadState.cleaning_operations.length()} checks changed something in your file.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                rx.icon("wand-sparkles", class_name="h-3.5 w-3.5"),
                "Applied before any metric",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.div(
            rx.foreach(UploadState.cleaning_operations, _operation_row),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def profiler_summary() -> rx.Component:
    """Compact profiler block used on the upload page."""
    return rx.el.div(
        profiler_score_card(),
        profiler_metric_grid(),
        class_name="flex flex-col gap-6 w-full",
    )


def profiler_section() -> rx.Component:
    """Full smart data profiler used on the data quality page."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("microscope", class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Smart data profiler",
                    class_name="text-xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "A full profile of the file you uploaded — size, types, gaps, invalid values, outliers and everything we changed.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        profiler_score_card(),
        profiler_metric_grid(),
        business_columns_card(),
        column_profile_card(),
        cleaning_operations_card(),
        class_name="flex flex-col gap-6 w-full",
    )
