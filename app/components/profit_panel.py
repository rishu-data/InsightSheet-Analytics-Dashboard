import reflex as rx

from app.states.profit_state import ProfitRow, ProfitState


def _chart_frame(figure: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.plotly(
            data=figure,
            use_resize_handler=True,
            config={"displayModeBar": False, "responsive": True},
        ),
        class_name="w-full overflow-x-auto mt-4 min-w-[300px]",
    )


def _kpi_card(
    icon: str, label: str, value: rx.Var | str, caption: rx.Var | str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-2xl font-semibold text-gray-900 mt-3 truncate",
        ),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-1 truncate",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _profit_value_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("banknote", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Total profit", class_name="text-xs font-medium text-gray-500"
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            ProfitState.total_profit_signed,
            class_name=rx.cond(
                ProfitState.is_profitable,
                "text-2xl font-semibold text-green-600 mt-3 truncate",
                "text-2xl font-semibold text-red-500 mt-3 truncate",
            ),
        ),
        rx.el.p(
            f"On {ProfitState.total_revenue_display} of revenue",
            class_name="text-xs font-medium text-gray-400 mt-1 truncate",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def _growth_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("trending-up", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.span(
                "Profit change", class_name="text-xs font-medium text-gray-500"
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.p(
                rx.cond(ProfitState.has_trend, ProfitState.growth_display, "—"),
                class_name=rx.match(
                    ProfitState.growth_direction,
                    ("up", "text-2xl font-semibold text-green-600"),
                    ("down", "text-2xl font-semibold text-red-500"),
                    "text-2xl font-semibold text-gray-900",
                ),
            ),
            rx.match(
                ProfitState.growth_direction,
                (
                    "up",
                    rx.icon(
                        "arrow-up-right", class_name="h-4 w-4 text-green-600"
                    ),
                ),
                (
                    "down",
                    rx.icon(
                        "arrow-down-right", class_name="h-4 w-4 text-red-500"
                    ),
                ),
                rx.icon("minus", class_name="h-4 w-4 text-gray-400"),
            ),
            class_name="flex items-center gap-1.5 mt-3",
        ),
        rx.el.p(
            ProfitState.growth_caption,
            class_name="text-xs font-medium text-gray-400 mt-1 truncate",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def profit_kpi_grid() -> rx.Component:
    return rx.el.div(
        _profit_value_card(),
        _kpi_card(
            "percent",
            "Profit margin",
            ProfitState.margin_display,
            "Profit ÷ revenue",
        ),
        _kpi_card(
            "receipt-text",
            "Cost of sales",
            ProfitState.total_cost_display,
            f"{ProfitState.cost_share}% of revenue",
        ),
        _kpi_card(
            "calculator",
            "Profit per order",
            ProfitState.profit_per_order_display,
            ProfitState.order_caption,
        ),
        _growth_card(),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 w-full",
    )


def _summary_point(point: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"),
        rx.el.span(point, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def profit_summary_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Profit summary",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Written from your own columns — nothing here is estimated.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                rx.icon("square_function", class_name="h-3.5 w-3.5"),
                ProfitState.method_formula,
                class_name="flex items-center gap-1.5 w-fit max-w-full rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600 truncate",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
            ),
            rx.el.p(
                f"{ProfitState.method_label}. {ProfitState.cost_basis}. {ProfitState.rows_used} row(s) had everything needed.",
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mb-4",
        ),
        rx.el.ul(
            rx.foreach(ProfitState.summary_points, _summary_point),
            class_name="flex flex-col gap-2.5",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def profit_trend_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("chart-column", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Profit & margin by month",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    rx.cond(
                        ProfitState.has_trend,
                        f"{ProfitState.months_covered} month(s) · best {ProfitState.best_month} at {ProfitState.best_month_display}",
                        "Bars show profit, the line shows margin percentage.",
                    ),
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            ProfitState.has_trend,
            _chart_frame(ProfitState.profit_trend_figure),
            rx.el.div(
                rx.icon("calendar-off", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "Map a date column with readable dates to chart profit over time.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-56 mt-4 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
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
                rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
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


def profit_ranking_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _rank_card(
                "Most profitable products",
                "Profit and margin for each mapped product or category.",
                "package",
                ProfitState.product_profit_figure,
                ProfitState.has_product_profit,
                "Map a product or category column on the upload page to rank profit by product.",
            ),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        rx.el.div(
            _rank_card(
                "Most profitable customers",
                "Profit and margin for each mapped customer.",
                "user-round",
                ProfitState.customer_profit_figure,
                ProfitState.has_customer_profit,
                "Map a customer column on the upload page to rank profit by customer.",
            ),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        class_name="flex flex-col lg:flex-row gap-6 w-full",
    )


def _tile(
    label: str, value: rx.Var | str, caption: rx.Var | str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-xl font-semibold text-gray-900 mt-2 truncate",
        ),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-0.5 truncate",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def _margin_badge(tone: rx.Var, text: rx.Var) -> rx.Component:
    return rx.el.span(
        text,
        class_name=rx.match(
            tone,
            (
                "loss",
                "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
            ),
            (
                "low",
                "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
            ),
            "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
        ),
    )


def _th(icon: str, label: rx.Var | str, right: bool) -> rx.Component:
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


def _margin_row(row: ProfitRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            row["name"],
            class_name="px-4 py-3 text-sm font-semibold text-gray-900 whitespace-nowrap",
        ),
        rx.el.td(
            row["revenue_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["cost_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["profit_display"],
            class_name="px-4 py-3 text-sm font-semibold text-gray-900 whitespace-nowrap text-right",
        ),
        rx.el.td(
            _margin_badge(row["tone"], row["margin_display"]),
            class_name="px-4 py-3 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["share_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        class_name="hover:bg-indigo-50/40 even:bg-gray-50/60 transition-colors",
    )


def margin_insights_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Margin insights",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Where your margin is strongest, and where you are selling close to or below cost.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            _tile(
                "Highest margin",
                rx.cond(
                    ProfitState.has_margin_table,
                    ProfitState.best_margin_display,
                    "—",
                ),
                rx.cond(
                    ProfitState.has_margin_table,
                    ProfitState.best_margin_name,
                    "Map a product or customer column",
                ),
                "arrow-up-right",
            ),
            _tile(
                "Lowest margin",
                rx.cond(
                    ProfitState.has_margin_table,
                    ProfitState.worst_margin_display,
                    "—",
                ),
                rx.cond(
                    ProfitState.has_margin_table,
                    ProfitState.worst_margin_name,
                    "Map a product or customer column",
                ),
                "arrow-down-right",
            ),
            _tile(
                "Rows below cost",
                ProfitState.loss_rows.to_string(),
                f"{ProfitState.loss_amount_display} lost on those rows",
                "circle-alert",
            ),
            _tile(
                "Loss-making items",
                rx.cond(
                    ProfitState.has_margin_table,
                    ProfitState.loss_items.to_string(),
                    "—",
                ),
                "Grouped totals under zero profit",
                "package-x",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4",
        ),
        rx.cond(
            ProfitState.has_margin_table,
            rx.el.div(
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                _th(
                                    "table",
                                    ProfitState.margin_table_label,
                                    False,
                                ),
                                _th("dollar-sign", "Revenue", True),
                                _th("receipt-text", "Cost", True),
                                _th("banknote", "Profit", True),
                                _th("percent", "Margin", True),
                                _th("chart-pie", "Share of profit", True),
                            ),
                            class_name="bg-gray-50 border-b border-gray-200",
                        ),
                        rx.el.tbody(
                            rx.foreach(ProfitState.margin_table, _margin_row),
                            class_name="divide-y divide-gray-100",
                        ),
                        class_name="table-auto min-w-full",
                    ),
                    class_name="overflow-x-auto",
                ),
                class_name="rounded-xl border border-gray-200 overflow-hidden mt-5",
            ),
            rx.el.div(
                rx.icon("table-2", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "Map a product or customer column on the upload page to break margins down line by line.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-40 mt-5 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
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


def profit_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("banknote", class_name="h-4 w-4 text-gray-400"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Profit analysis unavailable",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    ProfitState.blocked_reason,
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            ProfitState.missing_hints.length() > 0,
            rx.el.div(
                rx.el.p(
                    "To calculate profit we need one of these in your file:",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.ul(
                    rx.foreach(ProfitState.missing_hints, _missing_hint),
                    class_name="flex flex-col gap-2 mt-3",
                ),
                class_name="rounded-xl border border-gray-200 bg-gray-50/70 p-4 mt-4",
            ),
        ),
        rx.el.div(
            rx.icon(
                "shield-check",
                class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                "We never guess costs or margins — profit stays hidden until your data can support it.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-white p-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _profit_body() -> rx.Component:
    return rx.el.div(
        profit_kpi_grid(),
        profit_summary_card(),
        profit_trend_card(),
        profit_ranking_row(),
        margin_insights_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def profit_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("banknote", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Profit analysis",
                    class_name="text-xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "Profit, margin and cost figures derived only from columns that exist in your file.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(ProfitState.available, _profit_body(), profit_unavailable()),
        class_name="flex flex-col gap-6 w-full",
    )
