import reflex as rx

from app.states.dashboard_state import DashboardState, QualityCheck


def _check_row(check: QualityCheck) -> rx.Component:
    return rx.el.li(
        rx.icon(
            rx.cond(check["flagged"], "triangle-alert", "circle-check"),
            class_name=rx.cond(
                check["flagged"],
                "h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                "h-4 w-4 text-green-600 shrink-0 mt-0.5",
            ),
        ),
        rx.el.div(
            rx.el.p(
                check["label"],
                class_name="text-sm font-semibold text-gray-900",
            ),
            rx.el.p(
                check["detail"],
                class_name="text-xs font-medium text-gray-600 mt-0.5",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 rounded-xl border border-gray-200 bg-white p-3",
    )


def _banner() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("triangle-alert", class_name="h-5 w-5 text-yellow-600"),
                class_name="flex items-center justify-center h-10 w-10 rounded-xl bg-yellow-100 shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    DashboardState.large_change_title,
                    class_name="text-base font-semibold text-gray-900",
                ),
                rx.el.p(
                    DashboardState.large_change_message,
                    class_name="text-sm font-medium text-yellow-700 mt-0.5",
                ),
                rx.el.p(
                    f"{DashboardState.comparison_label} is {DashboardState.growth_display} \u00b7 {DashboardState.growth_caption}",
                    class_name="text-xs font-medium text-gray-600 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.icon("search-check", class_name="h-3.5 w-3.5"),
                rx.cond(
                    DashboardState.large_change_anomaly,
                    "Data-quality issue found",
                    "Data-quality checks passed",
                ),
                class_name=rx.cond(
                    DashboardState.large_change_anomaly,
                    "flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700",
                    "flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
                ),
            ),
            class_name="flex flex-wrap items-start gap-3",
        ),
        rx.el.ul(
            rx.foreach(DashboardState.large_change_checks, _check_row),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-4",
        ),
        rx.el.p(
            DashboardState.large_change_conclusion,
            class_name="text-sm font-medium text-gray-600 mt-4",
        ),
        class_name="rounded-2xl border border-yellow-200 bg-yellow-50/70 p-6 shadow-sm w-full",
    )


def large_change_warning() -> rx.Component:
    """Shown only when comparable-period revenue moves more than 30%."""
    return rx.cond(DashboardState.large_change_detected, _banner())
