import reflex as rx

from app.states.dashboard_tab_state import DashboardTabState

_ACTIVE = "flex items-center gap-2 shrink-0 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-blue-700 border border-gray-200 shadow-sm transition-colors"
_IDLE = "flex items-center gap-2 shrink-0 rounded-xl px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-white/70 transition-colors"


def _tab_button(value: str, label: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        rx.el.span(label),
        on_click=lambda: DashboardTabState.select_tab(value),
        class_name=rx.cond(DashboardTabState.active == value, _ACTIVE, _IDLE),
    )


def dashboard_tabs() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _tab_button("overview", "Overview", "layout-dashboard"),
            _tab_button("revenue", "Revenue Analytics", "chart-line"),
            _tab_button("customers", "Customer Intelligence", "users-round"),
            _tab_button("products", "Product Analytics", "package"),
            _tab_button("forecast", "Forecast", "trending-up"),
            _tab_button("ask", "Ask InsightSheet", "circle-help"),
            _tab_button("report", "Executive Report", "file-text"),
            _tab_button("quality", "Data Quality", "shield-check"),
            class_name="flex items-center gap-1 overflow-x-auto rounded-2xl border border-gray-200 bg-gray-50 p-1.5",
        ),
        class_name="w-full",
    )
