import reflex as rx

from app.states.insight_state import Insight, InsightState, Suggestion


def _tone_icon_wrap(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        (
            "good",
            "flex items-center justify-center h-8 w-8 rounded-lg bg-green-100 text-green-600 shrink-0",
        ),
        (
            "warn",
            "flex items-center justify-center h-8 w-8 rounded-lg bg-yellow-100 text-yellow-600 shrink-0",
        ),
        (
            "bad",
            "flex items-center justify-center h-8 w-8 rounded-lg bg-red-100 text-red-500 shrink-0",
        ),
        "flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 shrink-0",
    )


def _tone_metric_class(tone: rx.Var) -> rx.Var:
    return rx.match(
        tone,
        ("good", "text-lg font-semibold text-green-600 truncate"),
        ("warn", "text-lg font-semibold text-yellow-600 truncate"),
        ("bad", "text-lg font-semibold text-red-500 truncate"),
        "text-lg font-semibold text-gray-900 truncate",
    )


def _category_badge(category: rx.Var, tone: rx.Var) -> rx.Component:
    return rx.el.span(
        category,
        class_name=rx.match(
            tone,
            (
                "good",
                "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
            ),
            (
                "warn",
                "w-fit rounded-md bg-yellow-100 px-2 py-0.5 text-xs font-semibold text-yellow-600",
            ),
            (
                "bad",
                "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-500",
            ),
            "w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600",
        ),
    )


def _insight_card(item: Insight) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4"),
                class_name=_tone_icon_wrap(item["tone"]),
            ),
            rx.el.div(
                _category_badge(item["category"], item["tone"]),
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
            rx.el.p(
                item["metric_label"],
                class_name="text-xs font-medium text-gray-400",
            ),
            rx.el.p(
                item["metric_value"],
                class_name=_tone_metric_class(item["tone"]),
            ),
            class_name="mt-4 pt-4 border-t border-gray-100 min-w-0",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def _stat_pill(icon: str, label: rx.Var | str, tone: str) -> rx.Component:
    return rx.el.span(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        label,
        class_name={
            "indigo": "flex items-center gap-1.5 w-fit rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600",
            "green": "flex items-center gap-1.5 w-fit rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-600",
            "amber": "flex items-center gap-1.5 w-fit rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-600",
            "gray": "flex items-center gap-1.5 w-fit max-w-full rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 truncate",
        }[tone],
    )


def insights_header_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "What your data is telling you",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Every statement below is calculated from the rows currently in view — nothing is estimated or forecast.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _stat_pill(
                    "lightbulb",
                    f"{InsightState.insight_count} insights",
                    "indigo",
                ),
                _stat_pill(
                    "arrow-up-right",
                    f"{InsightState.positive_signals} positive",
                    "green",
                ),
                _stat_pill(
                    "triangle-alert",
                    f"{InsightState.risk_signals} to watch",
                    "amber",
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
            ),
            rx.el.div(
                rx.el.p(
                    InsightState.basis_note,
                    class_name="text-sm font-medium text-gray-600",
                ),
                rx.el.p(
                    f"Period analysed: {InsightState.period_label}",
                    class_name="text-xs font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def insights_grid() -> rx.Component:
    return rx.cond(
        InsightState.has_insights,
        rx.el.div(
            rx.foreach(InsightState.insights, _insight_card),
            class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 w-full",
        ),
        rx.el.div(
            rx.icon("search-x", class_name="h-5 w-5 text-gray-400"),
            rx.el.p(
                "No pattern was strong enough to report from the rows currently in view.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex flex-col items-center justify-center gap-2 h-40 rounded-2xl border border-dashed border-gray-300 bg-gray-50/60 text-center px-6 w-full",
        ),
    )


def _priority_badge(priority: rx.Var) -> rx.Component:
    return rx.el.span(
        priority,
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


def _suggestion_card(item: Suggestion) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        rx.icon("sparkles", class_name="h-3 w-3"),
                        "Suggestion",
                        class_name="flex items-center gap-1 w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
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
                item["basis"],
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-100 bg-gray-50/70 p-3 mt-4",
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def recommended_actions() -> rx.Component:
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
                        "Recommended actions",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        f"{InsightState.suggestion_count} suggestion(s) based only on the patterns detected above.",
                        class_name="text-sm font-medium text-gray-500",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            _stat_pill("sparkles", "Suggestions, not instructions", "gray"),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "circle-alert",
                class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5",
            ),
            rx.el.p(
                "These are suggestions generated from your own numbers. They are not predictions, "
                "targets or advice — review each one against what you know about your business.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-4",
        ),
        rx.cond(
            InsightState.has_suggestions,
            rx.el.div(
                rx.foreach(InsightState.suggestions, _suggestion_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-5 w-5 text-gray-400"),
                rx.el.p(
                    "No action is suggested — nothing in the current selection stands out as needing attention.",
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


def insights_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("lightbulb", class_name="h-4 w-4 text-gray-400"),
                class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Automated insights unavailable",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    InsightState.blocked_reason,
                    class_name="text-sm font-medium text-gray-500 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            InsightState.missing_hints.length() > 0,
            rx.el.div(
                rx.el.p(
                    "To read patterns out of your file we need:",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.ul(
                    rx.foreach(InsightState.missing_hints, _missing_hint),
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
                "We never invent trends. Insights stay hidden until your own rows can support them.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-white p-4 mt-4",
        ),
        rx.el.a(
            rx.icon("columns-3", class_name="h-4 w-4"),
            "Adjust column mapping",
            href="/",
            class_name="flex items-center gap-2 w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _insights_body() -> rx.Component:
    return rx.el.div(
        insights_header_card(),
        insights_grid(),
        recommended_actions(),
        class_name="flex flex-col gap-6 w-full",
    )


def insights_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("lightbulb", class_name="h-4 w-4 text-indigo-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Automated insights",
                    class_name="text-xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "Trends, anomalies, concentration and customer inactivity detected in the rows currently in view.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.cond(
            InsightState.available, _insights_body(), insights_unavailable()
        ),
        class_name="flex flex-col gap-6 w-full",
    )
