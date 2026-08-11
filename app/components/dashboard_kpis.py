import reflex as rx

from app.states.dashboard_state import KPI, DashboardState, Highlight


def _tone_icon(tone: rx.Var) -> rx.Component:
    return rx.match(
        tone,
        (
            "up",
            rx.icon("arrow-up-right", class_name="h-4 w-4 text-green-600"),
        ),
        (
            "down",
            rx.icon("arrow-down-right", class_name="h-4 w-4 text-red-500"),
        ),
        rx.fragment(),
    )


def _kpi_card(card: KPI) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(card["icon"], class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.span(
                card["label"],
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.cond(
            card["available"],
            rx.el.div(
                rx.el.p(
                    card["value"],
                    class_name=rx.match(
                        card["tone"],
                        (
                            "up",
                            "text-2xl font-semibold text-green-600 truncate",
                        ),
                        (
                            "down",
                            "text-2xl font-semibold text-red-500 truncate",
                        ),
                        "text-2xl font-semibold text-gray-900 truncate",
                    ),
                ),
                _tone_icon(card["tone"]),
                class_name="flex items-center gap-1.5 mt-3 min-w-0",
            ),
            rx.el.div(
                rx.icon(
                    "circle-slash", class_name="h-4 w-4 text-gray-400 shrink-0"
                ),
                rx.el.p(
                    card["value"],
                    class_name="text-sm font-semibold text-gray-500",
                ),
                class_name="flex items-start gap-2 mt-3",
            ),
        ),
        rx.el.p(
            card["caption"],
            class_name=rx.cond(
                card["available"],
                "text-xs font-medium text-gray-400 mt-1 truncate",
                "text-xs font-medium text-gray-400 mt-1",
            ),
        ),
        class_name=rx.cond(
            card["available"],
            "w-full rounded-2xl border border-gray-200 bg-white p-4 shadow-sm",
            "w-full rounded-2xl border border-dashed border-gray-300 bg-gray-50/60 p-4",
        ),
    )


def kpi_grid() -> rx.Component:
    return rx.el.div(
        rx.foreach(DashboardState.kpi_cards, _kpi_card),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 w-full",
    )


def _highlight_card(card: Highlight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(card["icon"], class_name="h-4 w-4"),
                class_name=rx.match(
                    card["tone"],
                    (
                        "up",
                        "flex items-center justify-center h-8 w-8 rounded-lg bg-green-100 text-green-600 shrink-0",
                    ),
                    (
                        "down",
                        "flex items-center justify-center h-8 w-8 rounded-lg bg-red-100 text-red-500 shrink-0",
                    ),
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 text-blue-600 shrink-0",
                ),
            ),
            rx.el.span(
                card["label"],
                class_name="text-xs font-medium text-gray-500 truncate",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            card["value"],
            class_name=rx.cond(
                card["available"],
                rx.match(
                    card["tone"],
                    (
                        "up",
                        "text-lg font-semibold text-green-600 mt-3 truncate",
                    ),
                    (
                        "down",
                        "text-lg font-semibold text-red-500 mt-3 truncate",
                    ),
                    "text-lg font-semibold text-gray-900 mt-3 truncate",
                ),
                "text-sm font-semibold text-gray-500 mt-3",
            ),
        ),
        rx.el.p(
            card["detail"],
            class_name="text-xs font-medium text-gray-500 mt-1",
        ),
        class_name=rx.cond(
            card["available"],
            "w-full rounded-xl border border-gray-200 bg-white p-4",
            "w-full rounded-xl border border-dashed border-gray-300 bg-gray-50/60 p-4",
        ),
    )


def _summary_point(point: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="h-4 w-4 text-blue-600 shrink-0 mt-0.5"),
        rx.el.span(point, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def executive_summary() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Executive summary",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Every line below is calculated from the filtered rows only.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.cond(
                    DashboardState.filters_applied > 0,
                    rx.el.span(
                        rx.icon("sliders-horizontal", class_name="h-3.5 w-3.5"),
                        f"{DashboardState.filtered_rows} of {DashboardState.source_rows} rows",
                        class_name="flex items-center gap-1.5 w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700",
                    ),
                ),
                rx.cond(
                    DashboardState.source_name != "",
                    rx.el.span(
                        rx.icon("file-spreadsheet", class_name="h-3.5 w-3.5"),
                        DashboardState.source_name,
                        class_name="flex items-center gap-1.5 w-fit max-w-full rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 truncate",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.div(
            rx.foreach(DashboardState.executive_highlights, _highlight_card),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-5",
        ),
        rx.el.div(
            rx.el.p(
                "Supporting detail",
                class_name="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3",
            ),
            rx.el.ul(
                rx.foreach(DashboardState.summary_points, _summary_point),
                class_name="flex flex-col gap-2.5",
            ),
            class_name="pt-5 border-t border-gray-100",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )
