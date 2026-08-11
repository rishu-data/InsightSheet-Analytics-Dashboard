import reflex as rx

from app.states.forecast_state import ForecastRow, ForecastState

_TAB_ACTIVE = "px-3.5 py-1.5 rounded-lg bg-white text-xs font-semibold text-indigo-700 border border-gray-200 transition-colors"
_TAB_IDLE = "px-3.5 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:text-gray-900 transition-colors"


def _horizon_button(months: int) -> rx.Component:
    return rx.el.button(
        f"{months} months",
        on_click=lambda: ForecastState.select_horizon(months),
        class_name=rx.cond(
            ForecastState.horizon == months, _TAB_ACTIVE, _TAB_IDLE
        ),
    )


def _horizon_switcher() -> rx.Component:
    return rx.el.div(
        _horizon_button(3),
        _horizon_button(6),
        _horizon_button(12),
        class_name="flex items-center gap-1 rounded-xl border border-gray-200 bg-gray-50 p-1 w-fit",
    )


def _estimate_pill() -> rx.Component:
    return rx.el.span(
        rx.icon("triangle-alert", class_name="h-3.5 w-3.5"),
        "Estimates only — not guaranteed",
        class_name="flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
    )


def _confidence_pill() -> rx.Component:
    return rx.el.span(
        rx.icon("gauge", class_name="h-3.5 w-3.5"),
        f"{ForecastState.confidence_label} confidence",
        class_name=rx.match(
            ForecastState.confidence_tone,
            (
                "good",
                "flex items-center gap-1.5 w-fit rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
            ),
            (
                "info",
                "flex items-center gap-1.5 w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-600",
            ),
            "flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
        ),
    )


def forecast_header_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "trending-up", class_name="h-5 w-5 text-indigo-600"
                    ),
                    class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-indigo-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Revenue Forecast",
                        class_name="text-2xl font-semibold tracking-tight text-gray-900",
                    ),
                    rx.el.p(
                        "Projected from the monthly revenue calculated out of the rows currently in view.",
                        class_name="text-sm font-medium text-gray-500 mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.div(
                _estimate_pill(),
                rx.cond(ForecastState.available, _confidence_pill()),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
            ),
            rx.el.p(
                "Forecasts are statistical estimates fitted to your own complete months of revenue. "
                "They are not predictions of certainty, targets or advice — treat every figure below "
                "as an estimate that assumes your current pattern continues.",
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _direction_icon(direction: rx.Var) -> rx.Component:
    return rx.match(
        direction,
        ("up", rx.icon("arrow-up-right", class_name="h-4 w-4 text-green-600")),
        (
            "down",
            rx.icon("arrow-down-right", class_name="h-4 w-4 text-red-500"),
        ),
        rx.icon("minus", class_name="h-4 w-4 text-gray-400"),
    )


def _value_class(direction: rx.Var) -> rx.Var:
    return rx.match(
        direction,
        ("up", "text-2xl font-semibold text-green-600 truncate"),
        ("down", "text-2xl font-semibold text-red-500 truncate"),
        "text-2xl font-semibold text-gray-900 truncate",
    )


def _kpi_card(
    icon: str,
    label: str,
    value: rx.Var | str,
    caption: rx.Var | str,
    tag: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                label, class_name="text-xs font-medium text-gray-500 truncate"
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            value,
            class_name="text-2xl font-semibold text-gray-900 mt-3 truncate",
        ),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        rx.el.span(
            tag,
            class_name="w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500 mt-3",
        ),
        class_name="w-full flex flex-col items-start rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _next_month_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("calendar-clock", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Forecast next month",
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            ForecastState.next_month_display,
            class_name="text-2xl font-semibold text-gray-900 mt-3 truncate",
        ),
        rx.el.div(
            _direction_icon(ForecastState.next_month_direction),
            rx.el.span(
                ForecastState.next_month_change_display,
                class_name=rx.match(
                    ForecastState.next_month_direction,
                    ("up", "text-xs font-semibold text-green-600"),
                    ("down", "text-xs font-semibold text-red-500"),
                    "text-xs font-semibold text-gray-500",
                ),
            ),
            rx.el.span(
                f"vs {ForecastState.last_month_label}",
                class_name="text-xs font-medium text-gray-400 truncate",
            ),
            class_name="flex items-center gap-1.5 mt-1 min-w-0",
        ),
        rx.el.span(
            f"Estimate for {ForecastState.next_month_label}",
            class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600 mt-3",
        ),
        class_name="w-full flex flex-col items-start rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _three_month_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("calendar-range", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Forecast next 3 months",
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            ForecastState.three_month_display,
            class_name="text-2xl font-semibold text-gray-900 mt-3 truncate",
        ),
        rx.el.p(
            ForecastState.three_month_label,
            class_name="text-xs font-medium text-gray-400 mt-1 truncate",
        ),
        rx.el.span(
            "Estimated total",
            class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600 mt-3",
        ),
        class_name="w-full flex flex-col items-start rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _growth_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("percent", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Expected growth / decline",
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.div(
            rx.el.p(
                ForecastState.three_month_change_display,
                class_name=_value_class(ForecastState.three_month_direction),
            ),
            _direction_icon(ForecastState.three_month_direction),
            class_name="flex items-center gap-1.5 mt-3 min-w-0",
        ),
        rx.el.p(
            ForecastState.three_month_basis,
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        rx.el.span(
            "Estimated change",
            class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600 mt-3",
        ),
        class_name="w-full flex flex-col items-start rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _trend_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("chart-line", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Trend direction",
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.div(
            rx.el.p(
                ForecastState.trend_label,
                class_name=_value_class(ForecastState.trend_direction),
            ),
            _direction_icon(ForecastState.trend_direction),
            class_name="flex items-center gap-1.5 mt-3 min-w-0",
        ),
        rx.el.p(
            f"{ForecastState.trend_per_month_display} per month across {ForecastState.months_used} complete month(s)",
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        rx.el.span(
            f"Fit quality {ForecastState.fit_display}",
            class_name="w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500 mt-3",
        ),
        class_name="w-full flex flex-col items-start rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def forecast_kpi_grid() -> rx.Component:
    return rx.el.div(
        _next_month_card(),
        _three_month_card(),
        _growth_card(),
        _trend_card(),
        _kpi_card(
            "sigma",
            ForecastState.horizon_label,
            ForecastState.horizon_total_display,
            rx.cond(
                ForecastState.band_available,
                f"95% range {ForecastState.horizon_range}",
                "No uncertainty range available",
            ),
            "Estimated total",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 w-full",
    )


def forecast_chart_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Historical vs forecast revenue",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{ForecastState.months_used} complete month(s) of actuals ({ForecastState.history_start} → {ForecastState.history_end}) plus {ForecastState.horizon} forecast month(s).",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            _horizon_switcher(),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.span(
                rx.el.span(
                    class_name="h-0.5 w-5 rounded-full bg-blue-600 shrink-0"
                ),
                "Actual revenue",
                class_name="flex items-center gap-2 text-xs font-medium text-gray-600",
            ),
            rx.el.span(
                rx.el.span(
                    class_name="h-0.5 w-5 rounded-full bg-indigo-600 shrink-0 opacity-70"
                ),
                "Forecast (estimate)",
                class_name="flex items-center gap-2 text-xs font-medium text-gray-600",
            ),
            rx.cond(
                ForecastState.band_available,
                rx.el.span(
                    rx.el.span(
                        class_name="h-3 w-5 rounded-sm bg-indigo-600/15 border border-indigo-200 shrink-0"
                    ),
                    "95% prediction range",
                    class_name="flex items-center gap-2 text-xs font-medium text-gray-600",
                ),
            ),
            class_name="flex flex-wrap items-center gap-4 mt-4",
        ),
        rx.el.div(
            rx.plotly(
                data=ForecastState.figure,
                use_resize_handler=True,
                config={"displayModeBar": False, "responsive": True},
            ),
            class_name="w-full overflow-x-auto mt-3 min-w-[300px]",
        ),
        rx.cond(
            ForecastState.partial_month_note != "",
            rx.el.div(
                rx.icon(
                    "circle-alert",
                    class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    ForecastState.partial_month_note,
                    class_name="text-sm font-medium text-yellow-700",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 p-4 mt-4",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def confidence_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("gauge", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "How much to trust this forecast",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    ForecastState.method_note,
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Fit quality",
                    class_name="text-xs font-medium text-gray-500",
                ),
                rx.el.span(
                    ForecastState.fit_display,
                    class_name="text-xs font-semibold text-indigo-600",
                ),
                class_name="flex items-center justify-between",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-2 rounded-full bg-indigo-600 transition-all duration-500",
                    style={"width": ForecastState.fit_display},
                ),
                class_name="h-2 w-full rounded-full bg-gray-100 overflow-hidden mt-2",
            ),
            class_name="mt-5",
        ),
        rx.el.div(
            rx.icon(
                "search-check",
                class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                ForecastState.confidence_detail,
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-4",
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


def _change_badge(direction: rx.Var, text: rx.Var) -> rx.Component:
    return rx.el.span(
        text,
        class_name=rx.match(
            direction,
            (
                "up",
                "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
            ),
            (
                "down",
                "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
            ),
            "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
        ),
    )


def _forecast_row(row: ForecastRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["month"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    "Forecast",
                    class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                ),
                class_name="flex flex-col items-start gap-1",
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            row["value_display"],
            class_name="px-4 py-3 text-sm font-semibold text-gray-900 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["range_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-500 whitespace-nowrap text-right",
        ),
        rx.el.td(
            _change_badge(row["direction"], row["change_display"]),
            class_name="px-4 py-3 whitespace-nowrap text-right",
        ),
        class_name="hover:bg-indigo-50/40 even:bg-gray-50/60 transition-colors",
    )


def forecast_table_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Month-by-month forecast",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Every value is an estimate with a 95% prediction range where the data supports one.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            _th("calendar", "Month", False),
                            _th("dollar-sign", "Forecast revenue", True),
                            _th("move-vertical", "95% range", True),
                            _th("percent", "Change vs prior month", True),
                        ),
                        class_name="bg-gray-50 border-b border-gray-200",
                    ),
                    rx.el.tbody(
                        rx.foreach(ForecastState.forecast_rows, _forecast_row),
                        class_name="divide-y divide-gray-100",
                    ),
                    class_name="table-auto min-w-full",
                ),
                class_name="overflow-x-auto",
            ),
            class_name="rounded-xl border border-gray-200 overflow-hidden",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _summary_point(point: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"),
        rx.el.span(point, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def forecast_summary_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Forecast summary",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"Based on {ForecastState.months_used} complete month(s) averaging {ForecastState.average_month_display}.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            _estimate_pill(),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.ul(
            rx.foreach(ForecastState.summary_points, _summary_point),
            class_name="flex flex-col gap-2.5",
        ),
        rx.el.div(
            rx.icon(
                "shield-check",
                class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                "Forecast values are estimates calculated from your uploaded rows only. They are not "
                "guaranteed outcomes and should be reviewed against what you know about your business.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-5",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _missing_hint(hint: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon(
            "circle-dashed", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"
        ),
        rx.el.span(hint, class_name="text-sm font-medium text-gray-600"),
        class_name="flex items-start gap-2.5",
    )


def forecast_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "chart-no-axes-column", class_name="h-4 w-4 text-gray-400"
                ),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    ForecastState.blocked_reason,
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "No forecast is shown, because we never project revenue from data that can't support it.",
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            ForecastState.missing_hints.length() > 0,
            rx.el.div(
                rx.el.p(
                    "To forecast revenue we need:",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.ul(
                    rx.foreach(ForecastState.missing_hints, _missing_hint),
                    class_name="flex flex-col gap-2 mt-3",
                ),
                class_name="rounded-xl border border-gray-200 bg-gray-50/70 p-4 mt-4",
            ),
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("cloud-upload", class_name="h-4 w-4"),
                "Upload a longer export",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors",
            ),
            rx.el.a(
                rx.icon("columns-3", class_name="h-4 w-4"),
                "Adjust column mapping",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors",
            ),
            class_name="flex flex-wrap items-center gap-3 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _loading_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-28 rounded-2xl border border-gray-200 bg-gray-100 animate-pulse w-full"
        ),
        rx.el.div(
            class_name="h-80 rounded-2xl border border-gray-200 bg-gray-100 animate-pulse w-full"
        ),
        rx.el.div(
            class_name="h-40 rounded-2xl border border-gray-200 bg-gray-100 animate-pulse w-full"
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def _forecast_body() -> rx.Component:
    return rx.el.div(
        forecast_kpi_grid(),
        forecast_chart_card(),
        rx.el.div(
            rx.el.div(
                forecast_summary_card(),
                class_name="w-full lg:flex-1 min-w-0",
            ),
            rx.el.div(
                confidence_card(),
                class_name="w-full lg:flex-1 min-w-0",
            ),
            class_name="flex flex-col lg:flex-row gap-6 w-full",
        ),
        forecast_table_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def forecast_section() -> rx.Component:
    return rx.el.div(
        forecast_header_card(),
        rx.cond(
            ForecastState.is_computing,
            _loading_state(),
            rx.cond(
                ForecastState.available,
                _forecast_body(),
                forecast_unavailable(),
            ),
        ),
        class_name="flex flex-col gap-6 w-full",
    )
