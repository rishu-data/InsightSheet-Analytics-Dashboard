import reflex as rx

from app.states.dashboard_state import (
    CustomerRow,
    DashboardState,
    InactivityBucket,
    MonthRow,
)


def _tile(
    label: rx.Var | str, value: rx.Var | str, caption: rx.Var | str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
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


def _month_row(row: MonthRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    row["period"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.cond(
                    row["partial"],
                    rx.el.span(
                        "In progress",
                        class_name="w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
                    ),
                ),
                class_name="flex flex-col items-start gap-1",
            ),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        rx.el.td(
            row["revenue_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["orders"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            _change_badge(row["direction"], row["change_display"]),
            class_name="px-4 py-3 whitespace-nowrap text-right",
        ),
        class_name="hover:bg-blue-50/40 even:bg-gray-50/60 transition-colors",
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


def month_over_month_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Comparable-period revenue analysis",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.span(
                    rx.icon("calendar-range", class_name="h-3.5 w-3.5"),
                    DashboardState.comparison_label,
                    class_name=rx.cond(
                        DashboardState.latest_period_complete,
                        "flex items-center gap-1.5 w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700",
                        "flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-3",
            ),
            rx.el.p(
                rx.cond(
                    DashboardState.latest_period_complete,
                    "The latest month in your file is complete, so it is compared with the full month before it.",
                    "The latest month is still in progress, so equal month-to-date windows are compared instead of a partial month against a complete one.",
                ),
                class_name="text-sm font-medium text-gray-500 mt-1",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            _tile(
                "Latest month",
                DashboardState.latest_month,
                "Most recent month with rows",
                "calendar",
            ),
            _tile(
                "Latest revenue",
                DashboardState.latest_revenue_display,
                f"{DashboardState.latest_orders} orders",
                "dollar-sign",
            ),
            _tile(
                DashboardState.comparison_label,
                rx.cond(
                    DashboardState.has_growth,
                    DashboardState.growth_display,
                    "Not available",
                ),
                DashboardState.growth_caption,
                "trending-up",
            ),
            _tile(
                "Months of history",
                DashboardState.month_history.length().to_string(),
                "Shown in the table below",
                "history",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4",
        ),
        rx.cond(
            DashboardState.partial_month_note != "",
            rx.el.div(
                rx.icon(
                    "circle-alert",
                    class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    DashboardState.partial_month_note,
                    class_name="text-sm font-medium text-yellow-700",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 p-4 mt-4",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            _th("calendar", "Month", False),
                            _th("dollar-sign", "Revenue", True),
                            _th("receipt", "Orders", True),
                            _th("percent", "MoM change", True),
                        ),
                        class_name="bg-gray-50 border-b border-gray-200",
                    ),
                    rx.el.tbody(
                        rx.foreach(DashboardState.month_history, _month_row),
                        class_name="divide-y divide-gray-100",
                    ),
                    class_name="table-auto min-w-full",
                ),
                class_name="overflow-x-auto",
            ),
            class_name="rounded-xl border border-gray-200 overflow-hidden mt-5",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _bucket_tile(bucket: InactivityBucket) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(bucket["icon"], class_name="h-4 w-4 text-blue-600"),
            rx.el.span(
                bucket["label"],
                class_name="text-xs font-semibold text-gray-600",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            f"{bucket['customers']} customers",
            class_name="text-lg font-semibold text-gray-900 mt-2",
        ),
        rx.el.p(
            bucket["revenue_display"],
            class_name="text-sm font-semibold text-blue-700 mt-0.5",
        ),
        rx.el.p(
            f"{bucket['share_display']} of historical revenue from potentially inactive customers",
            class_name="text-xs font-medium text-gray-400 mt-1",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def _inactivity_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("hourglass", class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h3(
                    "Historical Revenue from Potentially Inactive Customers",
                    class_name="text-base font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"{DashboardState.inactive_customers} potentially inactive customer(s) hold "
                    f"{DashboardState.inactive_revenue_display} of historical revenue, split by how long they have been quiet.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.icon("info", class_name="h-4 w-4 text-blue-600 shrink-0 mt-0.5"),
            rx.el.p(
                DashboardState.inactive_note,
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-blue-100 bg-blue-50/60 p-4 mt-4",
        ),
        rx.cond(
            DashboardState.inactivity_buckets.length() > 0,
            rx.el.div(
                rx.foreach(DashboardState.inactivity_buckets, _bucket_tile),
                class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mt-4",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-4 w-4 text-green-600"),
                rx.el.p(
                    "No customer has been inactive for 60+ days in this selection.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                class_name="flex items-center gap-2 rounded-xl border border-gray-200 bg-white p-4 mt-4",
            ),
        ),
        class_name="rounded-xl border border-gray-200 bg-gray-50/70 p-5 mt-5",
    )


def _concentration_tile(
    label: rx.Var | str,
    share: rx.Var | str,
    revenue: rx.Var | str,
    caption: rx.Var | str,
    icon: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
            rx.el.span(label, class_name="text-xs font-medium text-gray-500"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            share,
            class_name="text-2xl font-semibold text-gray-900 mt-2",
        ),
        rx.el.p(
            revenue,
            class_name="text-sm font-semibold text-blue-700 mt-0.5 truncate",
        ),
        rx.el.p(
            caption,
            class_name="text-xs font-medium text-gray-400 mt-1 truncate",
        ),
        class_name="w-full rounded-xl border border-gray-200 bg-white p-4",
    )


def _concentration_badge() -> rx.Component:
    return rx.el.span(
        rx.icon("chart-pie", class_name="h-3.5 w-3.5"),
        DashboardState.concentration_level,
        class_name=rx.match(
            DashboardState.concentration_tone,
            (
                "up",
                "flex items-center gap-1.5 w-fit rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
            ),
            (
                "down",
                "flex items-center gap-1.5 w-fit rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-500",
            ),
            "flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
        ),
    )


def _concentration_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _concentration_tile(
                "Top 1 customer",
                f"{DashboardState.top1_share:.1f}%",
                DashboardState.top1_revenue_display,
                DashboardState.top1_name,
                "crown",
            ),
            _concentration_tile(
                f"Top {DashboardState.top5_count} customers",
                f"{DashboardState.top5_share:.1f}%",
                DashboardState.top5_revenue_display,
                f"of {DashboardState.concentration_customers} customers in view",
                "users-round",
            ),
            _concentration_tile(
                f"Top {DashboardState.top10_count} customers",
                f"{DashboardState.top10_share:.1f}%",
                DashboardState.top10_revenue_display,
                f"of {DashboardState.concentration_customers} customers in view",
                "users",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-3 gap-4",
        ),
        rx.el.div(
            rx.icon(
                "search-check",
                class_name="h-4 w-4 text-blue-600 shrink-0 mt-0.5",
            ),
            rx.el.p(
                DashboardState.concentration_detail,
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-blue-100 bg-blue-50/60 p-4 mt-4",
        ),
        rx.el.p(
            "Percentages are shares of the revenue in view, calculated from the mapped customer column only.",
            class_name="text-xs font-medium text-gray-400 mt-3",
        ),
        class_name="w-full",
    )


def customer_concentration_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Customer Concentration",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "How much of your revenue depends on your largest accounts.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.cond(DashboardState.has_concentration, _concentration_badge()),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.cond(
            DashboardState.has_concentration,
            _concentration_body(),
            rx.el.div(
                rx.icon("user-round-x", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    DashboardState.concentration_detail,
                    class_name="text-sm font-medium text-gray-500 max-w-md text-center",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-40 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _status_badge(status: rx.Var) -> rx.Component:
    return rx.el.span(
        status,
        class_name=rx.match(
            status,
            (
                "Inactive",
                "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
            ),
            (
                "At risk",
                "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
            ),
            "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
        ),
    )


def _customer_row(row: CustomerRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            row["name"],
            class_name="px-4 py-3 text-sm font-semibold text-gray-900 whitespace-nowrap",
        ),
        rx.el.td(
            row["last_order"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap",
        ),
        rx.el.td(
            row["days_since"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["orders"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            row["revenue_display"],
            class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap text-right",
        ),
        rx.el.td(
            _status_badge(row["status"]),
            class_name="px-4 py-3 whitespace-nowrap",
        ),
        class_name="hover:bg-blue-50/40 even:bg-gray-50/60 transition-colors",
    )


def retention_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Customer retention & inactivity",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                f"Days counted from the newest date in your file ({DashboardState.reference_date}). Potentially inactive means 60+ days without an order.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.cond(
            DashboardState.has_customer_data,
            rx.el.div(
                rx.el.div(
                    _tile(
                        "Active customers",
                        DashboardState.active_customers.to_string(),
                        "Ordered within the last 60 days",
                        "user-check",
                    ),
                    _tile(
                        "At risk (30–59 days)",
                        DashboardState.at_risk_customers.to_string(),
                        "Slowing down but not lost yet",
                        "user-round-search",
                    ),
                    _tile(
                        "Potentially inactive (60+ days)",
                        DashboardState.inactive_customers.to_string(),
                        f"{DashboardState.inactive_revenue_display} of historical revenue",
                        "user-x",
                    ),
                    _tile(
                        "Retention rate",
                        f"{DashboardState.retention_rate:.1f}%",
                        "Active ÷ all customers",
                        "heart-pulse",
                    ),
                    _tile(
                        "Repeat customers",
                        f"{DashboardState.repeat_rate:.1f}%",
                        f"{DashboardState.repeat_customers} ordered more than once",
                        "repeat",
                    ),
                    class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4",
                ),
                _inactivity_section(),
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    _th("user-round", "Customer", False),
                                    _th("calendar", "Last order", False),
                                    _th("clock", "Days since", True),
                                    _th("receipt", "Orders", True),
                                    _th("dollar-sign", "Revenue", True),
                                    _th("activity", "Status", False),
                                ),
                                class_name="bg-gray-50 border-b border-gray-200",
                            ),
                            rx.el.tbody(
                                rx.foreach(
                                    DashboardState.customer_activity,
                                    _customer_row,
                                ),
                                class_name="divide-y divide-gray-100",
                            ),
                            class_name="table-auto min-w-full",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name="rounded-xl border border-gray-200 overflow-hidden mt-5",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("user-round-x", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "Map a customer column on the upload page to see retention and inactivity.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center gap-2 h-40 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )
