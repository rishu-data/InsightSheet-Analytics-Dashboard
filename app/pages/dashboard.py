import reflex as rx

from app.components.dashboard_charts import (
    revenue_trend_card,
    top_customers_card,
    top_products_card,
)
from app.components.dashboard_filters import clear_filters_button, filter_bar
from app.components.dashboard_kpis import executive_summary, kpi_grid
from app.components.change_warning import large_change_warning
from app.components.dashboard_tables import (
    customer_concentration_card,
    month_over_month_card,
    retention_card,
)
from app.components.dashboard_tabs import dashboard_tabs
from app.components.ask_panel import ask_section
from app.components.forecast_panel import forecast_section
from app.components.insights_panel import insights_section
from app.components.profit_panel import (
    margin_insights_card,
    profit_section,
)
from app.components.quality_audit import quality_audit_section
from app.components.report_panel import report_section
from app.components.rfm_panel import rfm_section
from app.components.sidebar import page_shell
from app.states.dashboard_state import DashboardState
from app.states.dashboard_tab_state import DashboardTabState
from app.states.filter_state import FilterState
from app.states.upload_state import UploadState


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("chart-line", class_name="h-6 w-6 text-blue-600"),
            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-blue-50 mb-4",
        ),
        rx.el.h2(
            "No metrics to show yet",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.p(
            DashboardState.blocked_reason,
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        rx.el.div(
            rx.cond(
                FilterState.has_active,
                clear_filters_button(True),
                rx.el.a(
                    rx.icon("cloud-upload", class_name="h-4 w-4"),
                    "Go to upload",
                    href="/",
                    class_name="flex items-center gap-2 w-fit rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors",
                ),
            ),
            rx.el.button(
                rx.icon("flask-conical", class_name="h-4 w-4"),
                "Try demo dataset",
                on_click=UploadState.load_demo_and_generate,
                disabled=UploadState.is_parsing,
                class_name="flex items-center gap-2 w-fit rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-60 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-center gap-3 mt-5",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white px-6 py-16 shadow-sm w-full",
    )


def _section_header(icon: str, title: str, subtitle: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
            class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.h2(
                title,
                class_name="text-xl font-semibold tracking-tight text-gray-900",
            ),
            rx.el.p(subtitle, class_name="text-sm font-medium text-gray-500"),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 w-full",
    )


def _filtered_section(body: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.cond(FilterState.ready, filter_bar()),
        rx.cond(DashboardState.has_metrics, large_change_warning()),
        rx.cond(DashboardState.has_metrics, body, _empty_state()),
        class_name="flex flex-col gap-6 w-full",
    )


def _overview_body() -> rx.Component:
    return rx.el.div(
        executive_summary(),
        kpi_grid(),
        revenue_trend_card(),
        rx.el.div(
            rx.el.div(
                top_customers_card(), class_name="w-full lg:flex-1 min-w-0"
            ),
            rx.el.div(
                top_products_card(), class_name="w-full lg:flex-1 min-w-0"
            ),
            class_name="flex flex-col lg:flex-row gap-6 w-full",
        ),
        insights_section(),
        class_name="flex flex-col gap-6 w-full",
    )


def _revenue_body() -> rx.Component:
    return rx.el.div(
        _section_header(
            "chart-line",
            "Revenue analytics",
            "Revenue over time, month-over-month movement and the profit behind it.",
        ),
        revenue_trend_card(),
        month_over_month_card(),
        profit_section(),
        class_name="flex flex-col gap-6 w-full",
    )


def _customer_body() -> rx.Component:
    return rx.el.div(
        _section_header(
            "users-round",
            "Customer intelligence",
            "Who buys, who repeats, who has gone quiet and how they segment.",
        ),
        top_customers_card(),
        customer_concentration_card(),
        retention_card(),
        rfm_section(),
        class_name="flex flex-col gap-6 w-full",
    )


def _product_body() -> rx.Component:
    return rx.el.div(
        _section_header(
            "package",
            "Product analytics",
            "What sells, what it earns and where margin is strongest or weakest.",
        ),
        top_products_card(),
        margin_insights_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def _forecast_tab() -> rx.Component:
    return rx.el.div(
        rx.cond(FilterState.ready, filter_bar()),
        forecast_section(),
        class_name="flex flex-col gap-6 w-full",
    )


def _report_tab() -> rx.Component:
    return rx.el.div(
        rx.cond(FilterState.ready, filter_bar()),
        report_section(),
        class_name="flex flex-col gap-6 w-full",
    )


def _tab_content() -> rx.Component:
    return rx.match(
        DashboardTabState.active,
        ("revenue", _filtered_section(_revenue_body())),
        ("customers", _filtered_section(_customer_body())),
        ("products", _filtered_section(_product_body())),
        ("forecast", _forecast_tab()),
        ("ask", ask_section()),
        ("report", _report_tab()),
        ("quality", quality_audit_section()),
        _filtered_section(_overview_body()),
    )


def dashboard_page() -> rx.Component:
    return page_shell(
        "dashboard",
        "Dashboard",
        "Metrics calculated live from your cleaned rows",
        rx.el.div(
            dashboard_tabs(),
            _tab_content(),
            class_name="flex flex-col gap-6 w-full",
        ),
    )
