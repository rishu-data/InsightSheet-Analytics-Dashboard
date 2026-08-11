import reflex as rx

from app.components.data_profiler import profiler_summary
from app.components.layout import how_it_works, intro
from app.components.mapping_card import mapping_card
from app.components.preview_card import column_overview_card, preview_card
from app.components.quality_report import quality_report
from app.components.readiness_panel import cleaning_log_card, readiness_panel
from app.components.sidebar import page_shell
from app.components.upload_card import upload_card
from app.states.upload_state import UploadState


def _workspace() -> rx.Component:
    return rx.el.div(
        readiness_panel(),
        profiler_summary(),
        rx.el.div(
            rx.el.div(mapping_card(), class_name="w-full lg:flex-1 min-w-0"),
            rx.el.div(
                cleaning_log_card(), class_name="w-full lg:flex-1 min-w-0"
            ),
            class_name="flex flex-col lg:flex-row gap-6 w-full",
        ),
        quality_report(),
        column_overview_card(),
        preview_card(),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Ready for the numbers?",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"Every metric is calculated from the {UploadState.clean_rows} cleaned rows above — nothing is estimated.",
                    class_name="text-sm font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("layout-dashboard", class_name="h-4 w-4"),
                "Generate dashboard",
                on_click=UploadState.generate_dashboard,
                class_name="flex items-center gap-2 w-fit rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors shrink-0",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
        ),
        class_name="flex flex-col gap-6 w-full",
    )


def upload_body() -> rx.Component:
    return rx.el.div(
        intro(),
        upload_card(),
        rx.cond(UploadState.has_data, _workspace(), how_it_works()),
        class_name="flex flex-col gap-6 w-full",
    )


def upload_page() -> rx.Component:
    return page_shell(
        "upload",
        "Upload New File",
        "Bring a messy sales export and we'll clean it",
        upload_body(),
    )
