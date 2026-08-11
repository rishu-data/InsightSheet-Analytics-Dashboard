import reflex as rx

from app.states.report_state import ReportKPI, ReportSection, ReportState


def _grounded_pill() -> rx.Component:
    return rx.el.span(
        rx.icon("shield-check", class_name="h-3.5 w-3.5"),
        "Written only from your calculated rows",
        class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
    )


def report_header_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("file-text", class_name="h-5 w-5 text-indigo-600"),
                    class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-indigo-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Executive Report",
                        class_name="text-2xl font-semibold tracking-tight text-gray-900",
                    ),
                    rx.el.p(
                        "A shareable write-up of every figure on this dashboard, plus clean exports of the underlying data.",
                        class_name="text-sm font-medium text-gray-500 mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            _grounded_pill(),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
            ),
            rx.el.p(
                "The report is generated from the cleaned rows currently in view, so your dashboard "
                "filters apply. Nothing is estimated except the forecast section, which is clearly "
                "labelled — if a metric can't be calculated, the report says so instead of guessing.",
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _error_banner() -> rx.Component:
    return rx.cond(
        ReportState.error_message != "",
        rx.el.div(
            rx.icon(
                "triangle-alert",
                class_name="h-4 w-4 text-red-500 shrink-0 mt-0.5",
            ),
            rx.el.p(
                ReportState.error_message,
                class_name="text-sm font-medium text-red-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 mt-4",
        ),
    )


def _meta_tile(icon: str, label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-gray-900 mt-2 truncate",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def _generating_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="h-10 w-10 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"
            ),
            rx.el.p(
                "Building your executive report…",
                class_name="text-sm font-semibold text-gray-700 mt-4",
            ),
            rx.el.p(
                "Collecting KPIs, revenue, customers, products, forecast, insights and data quality.",
                class_name="text-sm font-medium text-gray-500 mt-1 text-center max-w-md",
            ),
            class_name="flex flex-col items-center",
        ),
        class_name="flex items-center justify-center rounded-xl border border-dashed border-indigo-200 bg-indigo-50/40 px-6 py-12 mt-5",
    )


def _report_meta() -> rx.Component:
    return rx.el.div(
        _meta_tile("clock", "Generated", ReportState.generated_at),
        _meta_tile("file-spreadsheet", "Source", ReportState.source_label),
        _meta_tile("calendar-range", "Period", ReportState.period_label),
        _meta_tile("rows-3", "Rows included", ReportState.rows_note),
        _meta_tile(
            "layers",
            "Report size",
            f"{ReportState.section_count} sections · {ReportState.page_count} pages · {ReportState.pdf_size_kb} KB",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mt-5",
    )


def _idle_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("file-text", class_name="h-5 w-5 text-indigo-600"),
            class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-indigo-50 mb-3",
        ),
        rx.el.p(
            "No report generated yet",
            class_name="text-sm font-semibold text-gray-900",
        ),
        rx.el.p(
            "Press “Generate Executive Report” and we'll assemble a nine-section write-up from the rows currently in view.",
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        class_name="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50/60 px-6 py-12 mt-5",
    )


def generate_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Generate the report",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Cover page, executive summary, KPI overview, revenue, customers, products, "
                    "forecast, insights, actions and data quality.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.cond(
                    ReportState.is_generating,
                    rx.el.div(
                        class_name="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin"
                    ),
                    rx.icon("sparkles", class_name="h-4 w-4"),
                ),
                rx.cond(
                    ReportState.is_generating,
                    "Generating…",
                    rx.cond(
                        ReportState.report_ready,
                        "Regenerate report",
                        "Generate Executive Report",
                    ),
                ),
                on_click=ReportState.generate_report,
                disabled=ReportState.is_generating,
                class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        _error_banner(),
        rx.cond(
            ReportState.is_generating,
            _generating_state(),
            rx.cond(ReportState.report_ready, _report_meta(), _idle_state()),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _export_button(
    icon: str,
    title: str,
    detail: rx.Var | str,
    on_click: rx.event.EventType,
    disabled: rx.Var,
    busy: rx.Var,
    primary: bool,
) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.cond(
                busy,
                rx.el.div(
                    class_name="h-4 w-4 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin"
                ),
                rx.icon(icon, class_name="h-4 w-4"),
            ),
            class_name=rx.cond(
                primary,
                "flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-600 text-white shrink-0",
                "flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-50 text-indigo-600 shrink-0",
            ),
        ),
        rx.el.div(
            rx.el.p(
                rx.cond(busy, "Preparing…", title),
                class_name="text-sm font-semibold text-gray-900 text-left",
            ),
            rx.el.p(
                detail,
                class_name="text-xs font-medium text-gray-500 text-left mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon("download", class_name="h-4 w-4 text-gray-400 shrink-0"),
        on_click=on_click,
        disabled=disabled,
        class_name="flex items-center gap-3 w-full rounded-xl border border-gray-200 bg-white p-4 hover:border-indigo-300 hover:bg-indigo-50/40 disabled:opacity-60 disabled:hover:border-gray-200 disabled:hover:bg-white transition-colors",
    )


def export_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Export options",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Take the report or the data with you. Exports contain your own cleaned values only.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("lock", class_name="h-3.5 w-3.5"),
                "Built in this session",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.div(
            _export_button(
                "file-text",
                "Download PDF Report",
                rx.cond(
                    ReportState.report_ready,
                    f"{ReportState.page_count} pages · {ReportState.pdf_size_kb} KB · generated {ReportState.generated_at}",
                    "Generate the report first to enable this download",
                ),
                ReportState.download_pdf,
                ~ReportState.report_ready | ReportState.is_generating,
                ReportState.is_generating,
                True,
            ),
            _export_button(
                "file-spreadsheet",
                "Download Cleaned CSV",
                f"All {ReportState.source_rows} cleaned rows, headers standardised",
                ReportState.download_csv,
                ReportState.exporting != "",
                ReportState.exporting == "csv",
                False,
            ),
            _export_button(
                "table",
                "Download Cleaned Excel",
                "The same cleaned rows as an .xlsx workbook",
                ReportState.download_excel,
                ReportState.exporting != "",
                ReportState.exporting == "excel",
                False,
            ),
            _export_button(
                "filter",
                "Download filtered dashboard data",
                ReportState.rows_note,
                ReportState.download_filtered,
                ReportState.exporting != "",
                ReportState.exporting == "filtered",
                False,
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-3",
        ),
        rx.el.p(
            "Exports are built from the rows in memory for this session — your original file is never stored or shared.",
            class_name="text-xs font-medium text-gray-400 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _kpi_row(card: ReportKPI) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                card["label"],
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            rx.cond(
                card["available"],
                rx.el.span(
                    rx.icon("circle-check", class_name="h-3.5 w-3.5"),
                    class_name="text-green-600 shrink-0",
                ),
                rx.el.span(
                    rx.icon("circle-slash", class_name="h-3.5 w-3.5"),
                    class_name="text-gray-400 shrink-0",
                ),
            ),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.el.p(
            card["value"],
            class_name=rx.cond(
                card["available"],
                "text-lg font-semibold text-gray-900 mt-2 truncate",
                "text-sm font-semibold text-gray-500 mt-2",
            ),
        ),
        rx.el.p(
            card["caption"],
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        class_name=rx.cond(
            card["available"],
            "w-full rounded-xl border border-gray-200 bg-white p-4",
            "w-full rounded-xl border border-dashed border-gray-300 bg-gray-50/60 p-4",
        ),
    )


def _section_line(line: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon(
            "circle-dot", class_name="h-3.5 w-3.5 text-indigo-600 shrink-0 mt-1"
        ),
        rx.el.span(line, class_name="text-sm font-medium text-gray-600"),
        class_name="flex items-start gap-2.5",
    )


def _section_card(section: ReportSection) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(section["icon"], class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    section["title"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    section["summary"],
                    class_name="text-xs font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                f"{section['lines'].length()} lines",
                class_name="w-fit shrink-0 rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.ul(
            rx.foreach(section["lines"], _section_line),
            class_name="flex flex-col gap-2 mt-4 pt-4 border-t border-gray-100",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def preview_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Report preview",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Exactly what the PDF contains — every line is a value calculated from your rows.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("file-check", class_name="h-3.5 w-3.5"),
                f"{ReportState.section_count} sections",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.p(
                "KPI overview",
                class_name="text-xs font-semibold uppercase tracking-wide text-gray-500",
            ),
            rx.el.div(
                rx.foreach(ReportState.kpis, _kpi_row),
                class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 mt-3",
            ),
            class_name="mt-5",
        ),
        rx.el.div(
            rx.foreach(ReportState.sections, _section_card),
            class_name="flex flex-col gap-4 mt-5",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def report_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("file-text", class_name="h-6 w-6 text-indigo-600"),
            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-indigo-50 mb-4",
        ),
        rx.el.h2(
            "Nothing to report on yet",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.p(
            ReportState.blocked_reason,
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("cloud-upload", class_name="h-4 w-4"),
                "Go to upload",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors",
            ),
            rx.el.a(
                rx.icon("columns-3", class_name="h-4 w-4"),
                "Adjust column mapping",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-center gap-3 mt-5",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white px-6 py-16 shadow-sm w-full",
    )


def _report_body() -> rx.Component:
    return rx.el.div(
        generate_card(),
        export_card(),
        rx.cond(ReportState.report_ready, preview_card()),
        class_name="flex flex-col gap-6 w-full",
    )


def report_section() -> rx.Component:
    return rx.el.div(
        report_header_card(),
        rx.cond(ReportState.available, _report_body(), report_unavailable()),
        class_name="flex flex-col gap-6 w-full",
    )
