import reflex as rx

from app.states.rfm_state import (
    ALL_SEGMENTS,
    RFMCustomer,
    RFMInsight,
    RFMRecommendation,
    RFMSegment,
    RFMState,
)


def _tone_badge_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "good",
            "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
        ),
        (
            "info",
            "w-fit rounded-md bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-600",
        ),
        (
            "warn",
            "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
        ),
        "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
    )


_ICON_TONES: dict[str, str] = {
    "indigo": "flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 shrink-0",
    "blue": "flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 text-blue-600 shrink-0",
    "green": "flex items-center justify-center h-8 w-8 rounded-lg bg-green-100 text-green-600 shrink-0",
    "amber": "flex items-center justify-center h-8 w-8 rounded-lg bg-yellow-100 text-yellow-600 shrink-0",
    "red": "flex items-center justify-center h-8 w-8 rounded-lg bg-red-100 text-red-500 shrink-0",
}

_VALUE_TONES: dict[str, str] = {
    "indigo": "text-2xl font-semibold text-gray-900 mt-3 truncate",
    "blue": "text-2xl font-semibold text-gray-900 mt-3 truncate",
    "green": "text-2xl font-semibold text-green-600 mt-3 truncate",
    "amber": "text-2xl font-semibold text-yellow-600 mt-3 truncate",
    "red": "text-2xl font-semibold text-red-500 mt-3 truncate",
}


def _kpi_card(
    icon: str,
    label: str,
    value: rx.Var | str,
    caption: rx.Var | str,
    tone: str = "indigo",
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4"),
                class_name=_ICON_TONES[tone],
            ),
            rx.el.span(
                label,
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(value, class_name=_VALUE_TONES[tone]),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
    )


def rfm_kpi_grid() -> rx.Component:
    return rx.el.div(
        _kpi_card(
            "users-round",
            "Total Customers",
            RFMState.customer_total.to_string(),
            f"Scored from {RFMState.rows_used} usable row(s)",
            "blue",
        ),
        _kpi_card(
            "crown",
            "Champions",
            RFMState.champion_customers.to_string(),
            f"{RFMState.champion_revenue_display} · {RFMState.champion_revenue_share} of scored revenue",
            "green",
        ),
        _kpi_card(
            "heart",
            "Loyal Customers",
            RFMState.loyal_customers.to_string(),
            f"{RFMState.loyal_revenue_display} of historical revenue",
            "green",
        ),
        _kpi_card(
            "triangle-alert",
            "At Risk",
            RFMState.at_risk_customers.to_string(),
            f"{RFMState.at_risk_revenue_display} of historical revenue · purchases have slowed",
            "amber",
        ),
        _kpi_card(
            "moon",
            "Potentially Inactive",
            RFMState.inactive_customers.to_string(),
            f"{RFMState.inactive_revenue_display} of historical revenue · segment label, not a predicted loss",
            "red",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 w-full",
    )


def rfm_average_grid() -> rx.Component:
    return rx.el.div(
        _kpi_card(
            "clock",
            "Average recency",
            f"{RFMState.avg_recency} days",
            f"Median {RFMState.median_recency} days · reference date {RFMState.reference_date}",
        ),
        _kpi_card(
            "repeat",
            "Average frequency",
            RFMState.avg_frequency_display,
            RFMState.frequency_basis,
        ),
        _kpi_card(
            "dollar-sign",
            "Average monetary value",
            RFMState.avg_monetary_display,
            f"{RFMState.total_revenue_display} across all scored customers",
        ),
        _kpi_card(
            "life-buoy",
            "Cannot Lose Them",
            RFMState.cannot_lose_customers.to_string(),
            f"{RFMState.cannot_lose_revenue_display} of historical revenue from high past spend",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 w-full",
    )


def _summary_point(point: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"),
        rx.el.span(point, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def _method_tile(
    icon: str, letter: str, title: str, detail: rx.Var | str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.span(
                    letter,
                    class_name="w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                ),
                rx.el.p(
                    title,
                    class_name="text-sm font-semibold text-gray-900 mt-1",
                ),
                class_name="min-w-0 flex flex-col items-start",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.p(
            detail,
            class_name="text-xs font-medium text-gray-500 mt-3",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def scoring_method_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "How the scores and segments are worked out",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Recency, frequency and monetary value are ranked into 1–5 scores from your own rows, then combined into practical segments.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                rx.icon("square_function", class_name="h-3.5 w-3.5"),
                "R = days since latest purchase · F = orders · M = total revenue",
                class_name="flex items-center gap-1.5 w-fit max-w-full rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600 truncate",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            _method_tile(
                "clock",
                "R",
                "Recency",
                f"Days between each customer's latest purchase and the latest valid transaction date in your file ({RFMState.reference_date}). Fewer days score higher.",
            ),
            _method_tile(
                "repeat",
                "F",
                "Frequency",
                f"{RFMState.frequency_basis}. More purchases score higher.",
            ),
            _method_tile(
                "dollar-sign",
                "M",
                "Monetary",
                "Total historical revenue per customer from the mapped revenue column. Higher spend scores higher.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5",
        ),
        rx.el.div(
            rx.icon(
                rx.cond(RFMState.scoring_simplified, "circle-alert", "info"),
                class_name=rx.cond(
                    RFMState.scoring_simplified,
                    "h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                    "h-4 w-4 text-indigo-600 shrink-0 mt-0.5",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    rx.cond(
                        RFMState.scoring_simplified,
                        "Scoring simplified for this dataset",
                        "Percentile (quantile) scoring",
                    ),
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    RFMState.scoring_note,
                    class_name="text-sm font-medium text-gray-600 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name=rx.cond(
                RFMState.scoring_simplified,
                "flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 p-4 mt-4",
                "flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-4",
            ),
        ),
        rx.el.ul(
            rx.foreach(RFMState.summary_points, _summary_point),
            class_name="flex flex-col gap-2.5 mt-5 pt-5 border-t border-gray-100",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _segment_card(segment: RFMSegment) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(segment["icon"], class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    segment["name"],
                    class_name="text-sm font-semibold text-gray-900 truncate",
                ),
                rx.el.span(
                    f"{segment['customers']} customers · {segment['share_display']}",
                    class_name=_tone_badge_class(segment["tone"]),
                ),
                class_name="min-w-0 flex flex-col gap-1 items-start",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.p(
            segment["description"],
            class_name="text-xs font-medium text-gray-500 mt-3",
        ),
        rx.el.div(
            rx.icon(
                "square_function",
                class_name="h-3.5 w-3.5 text-indigo-600 shrink-0 mt-0.5",
            ),
            rx.el.p(
                segment["rule"],
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-lg border border-gray-100 bg-gray-50/70 p-2.5 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Revenue", class_name="text-xs font-medium text-gray-400"
                ),
                rx.el.p(
                    segment["revenue_display"],
                    class_name="text-sm font-semibold text-gray-900 truncate",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Share of revenue",
                    class_name="text-xs font-medium text-gray-400",
                ),
                rx.el.p(
                    segment["revenue_share_display"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Avg recency",
                    class_name="text-xs font-medium text-gray-400",
                ),
                rx.el.p(
                    f"{segment['avg_recency']} days",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Avg orders",
                    class_name="text-xs font-medium text-gray-400",
                ),
                rx.el.p(
                    segment["avg_frequency_display"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Avg spend", class_name="text-xs font-medium text-gray-400"
                ),
                rx.el.p(
                    segment["avg_monetary_display"],
                    class_name="text-sm font-semibold text-gray-900 truncate",
                ),
                class_name="min-w-0",
            ),
            class_name="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-4 pt-4 border-t border-gray-100",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5",
    )


def segment_cards() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Segments found in your file",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "Only segments with at least one customer are shown.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.foreach(RFMState.segments, _segment_card),
            class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def segment_distribution_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("chart-column", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Customer Count by RFM Segment",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"Biggest group is {RFMState.top_segment} · most revenue comes from {RFMState.top_revenue_segment} ({RFMState.top_revenue_segment_display})",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.plotly(
                data=RFMState.segment_figure,
                use_resize_handler=True,
                config={"displayModeBar": False, "responsive": True},
            ),
            class_name="w-full overflow-x-auto mt-4 min-w-[300px]",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def segment_revenue_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("chart-pie", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Revenue by RFM Segment",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{RFMState.top_revenue_segment} contributes {RFMState.top_revenue_segment_display} ({RFMState.top_revenue_segment_share}) of {RFMState.total_revenue_display}",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.plotly(
                data=RFMState.segment_revenue_figure,
                use_resize_handler=True,
                config={"displayModeBar": False, "responsive": True},
            ),
            class_name="w-full overflow-x-auto mt-4 min-w-[300px]",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def segment_charts_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            segment_distribution_card(),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        rx.el.div(
            segment_revenue_card(),
            class_name="w-full lg:flex-1 min-w-0",
        ),
        class_name="flex flex-col lg:flex-row gap-6 w-full",
    )


def _sortable_th(key: str, icon: str, label: str, right: bool) -> rx.Component:
    return rx.el.th(
        rx.el.button(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-gray-400 shrink-0"),
            rx.el.span(label),
            rx.icon(
                rx.cond(
                    RFMState.sort_key == key,
                    rx.cond(RFMState.sort_desc, "arrow-down", "arrow-up"),
                    "chevrons-up-down",
                ),
                class_name=rx.cond(
                    RFMState.sort_key == key,
                    "h-3.5 w-3.5 text-indigo-600 shrink-0",
                    "h-3.5 w-3.5 text-gray-300 shrink-0",
                ),
            ),
            on_click=lambda: RFMState.sort_by(key),
            class_name=rx.cond(
                right,
                "flex items-center justify-end gap-2 w-full hover:text-indigo-700 transition-colors",
                "flex items-center gap-2 w-full hover:text-indigo-700 transition-colors",
            ),
        ),
        class_name=rx.cond(
            RFMState.sort_key == key,
            "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-indigo-700 whitespace-nowrap",
            "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap",
        ),
    )


def _customer_row(row: RFMCustomer) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["name"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    f"Last purchase {row['last_order']}",
                    class_name="text-xs font-medium text-gray-400",
                ),
                class_name="flex flex-col items-start gap-0.5 min-w-0",
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.span(
                row["segment"], class_name=_tone_badge_class(row["tone"])
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            f"{row['recency']} days",
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["frequency"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["monetary_display"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    f"{row['avg_order_display']} per order",
                    class_name="text-xs font-medium text-gray-400",
                ),
                class_name="flex flex-col items-end gap-0.5",
            ),
            class_name="px-4 py-3 whitespace-nowrap text-right",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["rfm"],
                    class_name="w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                ),
                rx.el.span(
                    f"total {row['score_total']} / 15",
                    class_name="text-xs font-medium text-gray-400",
                ),
                class_name="flex flex-col items-end gap-0.5",
            ),
            class_name="px-4 py-3 whitespace-nowrap text-right",
        ),
        class_name="hover:bg-indigo-50/40 even:bg-gray-50/60 transition-colors",
    )


def segment_filter_select() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("filter", class_name="h-3.5 w-3.5 text-indigo-600"),
            rx.el.span(
                "Customer Segment",
                class_name="text-xs font-semibold text-gray-600",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    RFMState.segment_options,
                    lambda option: rx.el.option(option, value=option),
                ),
                value=RFMState.selected_segment,
                on_change=RFMState.select_segment,
                class_name="w-full appearance-none rounded-xl border border-gray-300 bg-white px-4 py-2.5 pr-10 text-sm font-medium text-gray-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-hidden transition-colors cursor-pointer",
            ),
            rx.icon(
                "chevron-down",
                class_name="h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="w-full sm:w-56 min-w-0",
    )


def _search_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search", class_name="h-3.5 w-3.5 text-indigo-600"),
            rx.el.span(
                "Search customers",
                class_name="text-xs font-semibold text-gray-600",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Search by customer or segment",
                default_value=RFMState.search_query,
                on_change=RFMState.set_search.debounce(300),
                class_name="w-full rounded-xl border border-gray-300 bg-white pl-10 pr-4 py-2.5 text-sm font-medium text-gray-800 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-hidden transition-colors",
            ),
            rx.icon(
                "search",
                class_name="h-4 w-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="w-full sm:flex-1 min-w-0",
    )


def _sort_field() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("arrow-down-up", class_name="h-3.5 w-3.5 text-indigo-600"),
            rx.el.span(
                "Sort by",
                class_name="text-xs font-semibold text-gray-600",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option("Monetary value", value="monetary"),
                    rx.el.option("Recency (days)", value="recency"),
                    rx.el.option("Frequency", value="frequency"),
                    rx.el.option("RFM score", value="score"),
                    rx.el.option("Customer name", value="name"),
                    rx.el.option("Segment", value="segment"),
                    value=RFMState.sort_key,
                    on_change=RFMState.set_sort_key,
                    class_name="w-full appearance-none rounded-xl border border-gray-300 bg-white px-4 py-2.5 pr-10 text-sm font-medium text-gray-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-hidden transition-colors cursor-pointer",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
                ),
                class_name="relative flex-1 min-w-0",
            ),
            rx.el.button(
                rx.icon(
                    rx.cond(RFMState.sort_desc, "arrow-down", "arrow-up"),
                    class_name="h-4 w-4",
                ),
                rx.el.span(
                    RFMState.sort_direction_label,
                    class_name="hidden lg:inline",
                ),
                on_click=RFMState.toggle_sort_direction,
                class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl border border-gray-300 bg-white px-3.5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
            ),
            class_name="flex items-center gap-2 w-full mt-1.5",
        ),
        class_name="w-full sm:w-auto min-w-0",
    )


def _table_empty_state() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="h-5 w-5 text-gray-400"),
        rx.el.p(
            "No scored customer matches this search or segment.",
            class_name="text-sm font-medium text-gray-500",
        ),
        rx.el.button(
            rx.icon("filter-x", class_name="h-4 w-4"),
            "Reset search & segment",
            on_click=RFMState.clear_table_controls,
            class_name="flex items-center gap-2 w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors mt-1",
        ),
        class_name="flex flex-col items-center justify-center gap-2 h-48 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
    )


def _customer_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _sortable_th("name", "user-round", "Customer", False),
                        _sortable_th("segment", "tag", "Segment", False),
                        _sortable_th("recency", "clock", "Recency", True),
                        _sortable_th("frequency", "repeat", "Frequency", True),
                        _sortable_th(
                            "monetary", "dollar-sign", "Monetary", True
                        ),
                        _sortable_th("score", "hash", "RFM Score", True),
                    ),
                    class_name="bg-gray-50 border-b border-gray-200",
                ),
                rx.el.tbody(
                    rx.foreach(RFMState.visible_customers, _customer_row),
                    class_name="divide-y divide-gray-100",
                ),
                class_name="table-auto min-w-full",
            ),
            class_name="overflow-x-auto",
        ),
        class_name="rounded-xl border border-gray-200 overflow-hidden",
    )


def customer_table_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "RFM customer table",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    RFMState.visible_count_label,
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.cond(
                RFMState.table_controls_active,
                rx.el.button(
                    rx.icon("filter-x", class_name="h-4 w-4"),
                    "Clear search & segment",
                    on_click=RFMState.clear_table_controls,
                    class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
                ),
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            _search_field(),
            segment_filter_select(),
            _sort_field(),
            class_name="flex flex-col sm:flex-row sm:items-end gap-3 mt-4",
        ),
        rx.el.div(
            rx.cond(
                RFMState.selected_segment != ALL_SEGMENTS,
                rx.el.span(
                    rx.icon("check", class_name="h-3 w-3"),
                    f"Segment: {RFMState.selected_segment}",
                    class_name="flex items-center gap-1.5 w-fit rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700",
                ),
            ),
            rx.el.span(
                rx.icon("table-2", class_name="h-3 w-3"),
                f"{RFMState.match_count} matching customer(s)",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            rx.el.span(
                rx.icon("list", class_name="h-3 w-3"),
                "First 100 rows shown",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.el.div(
            rx.cond(
                RFMState.has_visible_customers,
                _customer_table(),
                _table_empty_state(),
            ),
            class_name="mt-4",
        ),
        rx.el.p(
            "Searching, filtering and sorting only change what is displayed — the scored values themselves are never altered.",
            class_name="text-xs font-medium text-gray-400 mt-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _insight_card(item: RFMInsight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4"),
                class_name=rx.match(
                    item["tone"],
                    (
                        "good",
                        "flex items-center justify-center h-8 w-8 rounded-lg bg-green-100 text-green-600 shrink-0",
                    ),
                    (
                        "warn",
                        "flex items-center justify-center h-8 w-8 rounded-lg bg-yellow-100 text-yellow-600 shrink-0",
                    ),
                    (
                        "risk",
                        "flex items-center justify-center h-8 w-8 rounded-lg bg-red-100 text-red-500 shrink-0",
                    ),
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 shrink-0",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    item["label"],
                    class_name="text-xs font-medium text-gray-500",
                ),
                rx.el.p(
                    item["value"],
                    class_name=rx.match(
                        item["tone"],
                        ("good", "text-lg font-semibold text-green-600"),
                        ("warn", "text-lg font-semibold text-yellow-600"),
                        ("risk", "text-lg font-semibold text-red-500"),
                        "text-lg font-semibold text-gray-900",
                    ),
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-sm font-medium text-gray-500 mt-3",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def rfm_insights_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("lightbulb", class_name="h-4 w-4 text-indigo-600"),
                    class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "RFM insights",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        "Every figure below is calculated from the scored rows currently in view.",
                        class_name="text-sm font-medium text-gray-500",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.span(
                rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                "Calculated, never estimated",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.cond(
            RFMState.has_insights,
            rx.el.div(
                rx.foreach(RFMState.insights, _insight_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4",
            ),
            rx.el.div(
                rx.icon("search-x", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "No RFM insight could be calculated from this selection.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-32 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _priority_badge(priority: rx.Var) -> rx.Component:
    return rx.el.span(
        f"{priority} priority",
        class_name=rx.match(
            priority,
            (
                "High",
                "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
            ),
            (
                "Medium",
                "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
            ),
            "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
        ),
    )


def _recommendation_card(item: RFMRecommendation) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        item["segment"],
                        class_name="w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                    ),
                    _priority_badge(item["priority"]),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-gray-900 mt-1.5",
                ),
                class_name="min-w-0 flex flex-col items-start",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-sm font-medium text-gray-500 mt-3",
        ),
        rx.el.div(
            rx.icon(
                "search-check",
                class_name="h-3.5 w-3.5 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                item["scope"],
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-100 bg-gray-50/70 p-3 mt-4",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def rfm_recommendations_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "list-checks", class_name="h-4 w-4 text-indigo-600"
                    ),
                    class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "RFM recommendations",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        "Suggested next steps for the segments that actually exist in your file.",
                        class_name="text-sm font-medium text-gray-500",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.span(
                rx.icon("sparkles", class_name="h-3.5 w-3.5"),
                "Recommendations, not guaranteed outcomes",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "circle-alert",
                class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                "These are recommendations generated from your own RFM scores. They are not "
                "predictions, targets or advice — review each one against what you know about "
                "your customers.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-4",
        ),
        rx.cond(
            RFMState.has_recommendations,
            rx.el.div(
                rx.foreach(RFMState.recommendations, _recommendation_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "No segment-specific recommendation applies to this selection.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-32 mt-4 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
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


def rfm_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("users-round", class_name="h-4 w-4 text-gray-400"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Customer Intelligence — RFM Analysis unavailable",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    RFMState.blocked_reason,
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            RFMState.missing_hints.length() > 0,
            rx.el.div(
                rx.el.p(
                    "To score customers we need these in your file:",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.ul(
                    rx.foreach(RFMState.missing_hints, _missing_hint),
                    class_name="flex flex-col gap-2 mt-3",
                ),
                class_name="rounded-xl border border-gray-200 bg-gray-50/70 p-4 mt-4",
            ),
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("columns-3", class_name="h-4 w-4"),
                "Adjust column mapping",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors",
            ),
            class_name="flex flex-wrap items-center gap-3 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _rfm_body() -> rx.Component:
    return rx.el.div(
        rfm_kpi_grid(),
        rfm_average_grid(),
        scoring_method_card(),
        segment_charts_row(),
        segment_cards(),
        customer_table_card(),
        rfm_insights_card(),
        rfm_recommendations_card(),
        class_name="flex flex-col gap-6 w-full",
    )


def rfm_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("users-round", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Customer Intelligence — RFM Analysis",
                    class_name="text-xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "Recency, frequency and monetary value scored from your mapped customer, date, revenue and order columns only.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(RFMState.available, _rfm_body(), rfm_unavailable()),
        class_name="flex flex-col gap-6 w-full",
    )
