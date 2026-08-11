import reflex as rx

from app.components.data_profiler import profiler_section
from app.components.preview_card import column_overview_card, preview_card
from app.components.quality_report import quality_report
from app.components.readiness_panel import cleaning_log_card, readiness_panel
from app.components.sidebar import page_shell
from app.states.upload_state import UploadState


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("shield-check", class_name="h-6 w-6 text-blue-600"),
            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-blue-50 mb-4",
        ),
        rx.el.h2(
            "No quality report yet",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.p(
            "Upload a spreadsheet and we'll show exactly what we changed, column by column — original vs cleaned rows, duplicates, missing values and invalid dates or amounts.",
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("cloud-upload", class_name="h-4 w-4"),
                "Go to upload",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors",
            ),
            rx.el.button(
                rx.icon("flask-conical", class_name="h-4 w-4"),
                "Try demo dataset",
                on_click=UploadState.load_demo,
                class_name="flex items-center gap-2 w-fit rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-100 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-center gap-3 mt-5",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white px-6 py-16 shadow-sm w-full",
    )


def _quality_body() -> rx.Component:
    return rx.el.div(
        readiness_panel(),
        profiler_section(),
        quality_report(),
        cleaning_log_card(),
        column_overview_card(),
        preview_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def data_quality_page() -> rx.Component:
    return page_shell(
        "quality",
        "Data Quality",
        "What we cleaned and how complete each column is",
        rx.cond(UploadState.has_data, _quality_body(), _empty_state()),
    )
