import reflex as rx

from app.states.dashboard_state import DashboardState

_TAB_ACTIVE = "px-3.5 py-1.5 rounded-lg bg-white text-xs font-semibold text-blue-700 border border-gray-200 transition-colors"
_TAB_IDLE = "px-3.5 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:text-gray-900 transition-colors"


def _granularity_button(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: DashboardState.select_granularity(label),
        class_name=rx.cond(
            DashboardState.granularity == label, _TAB_ACTIVE, _TAB_IDLE
        ),
    )


def _chart_frame(figure: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.plotly(
            data=figure,
            use_resize_handler=True,
            config={"displayModeBar": False, "responsive": True},
        ),
        class_name="w-full overflow-x-auto mt-4",
    )


def revenue_trend_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Revenue over time",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{DashboardState.trend_periods} {DashboardState.granularity.lower()} periods · peak {DashboardState.best_period_label} at {DashboardState.best_period_display}",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _granularity_button("Daily"),
                _granularity_button("Weekly"),
                _granularity_button("Monthly"),
                class_name="flex items-center gap-1 rounded-xl border border-gray-200 bg-gray-50 p-1 w-fit",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        _chart_frame(DashboardState.revenue_figure),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _rank_card(
    title: str,
    subtitle: str,
    icon: str,
    figure: rx.Var,
    available: rx.Var,
    hint: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    title, class_name="text-lg font-semibold text-gray-900"
                ),
                rx.el.p(
                    subtitle, class_name="text-sm font-medium text-gray-500"
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            available,
            _chart_frame(figure),
            rx.el.div(
                rx.icon(
                    "chart-no-axes-column", class_name="h-5 w-5 text-gray-400"
                ),
                rx.el.p(hint, class_name="text-sm font-medium text-gray-500"),
                class_name="flex flex-col items-center justify-center gap-2 h-56 mt-4 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def top_customers_card() -> rx.Component:
    return _rank_card(
        "Top customers by revenue",
        "Share of total revenue shown beside each bar.",
        "user-round",
        DashboardState.customer_figure,
        DashboardState.has_customer_data,
        "Map a customer column on the upload page to rank customers.",
    )


def top_products_card() -> rx.Component:
    return _rank_card(
        "Top products by revenue",
        "Share of total revenue shown beside each bar.",
        "package",
        DashboardState.product_figure,
        DashboardState.has_product_data,
        "Map a product or category column on the upload page to rank products.",
    )
