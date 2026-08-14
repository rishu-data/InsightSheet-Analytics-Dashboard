import reflex as rx

from app.components.sidebar import page_shell
from app.states.pricing_state import (
    FAQ_ITEMS,
    FREE_FEATURES,
    PRO_BUTTON_LABEL,
    PRO_FEATURES,
    PricingState,
)


def _intro() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("credit-card", class_name="h-5 w-5 text-blue-600"),
                class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.h2(
                    "Choose the Right Plan",
                    class_name="text-2xl font-semibold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "Start with powerful business analytics and upgrade when you need more.",
                    class_name="text-sm font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3 min-w-0",
        ),
        rx.el.span(
            rx.icon("lock", class_name="h-3.5 w-3.5"),
            "No card details are collected here",
            class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
        ),
        class_name="flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def _free_feature(feature: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="h-4 w-4 text-blue-600 shrink-0 mt-0.5"),
        rx.el.span(feature, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def _pro_feature(feature: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon(
            "circle-check",
            class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5",
        ),
        rx.el.span(feature, class_name="text-sm font-medium text-gray-700"),
        class_name="flex items-start gap-2.5",
    )


def _free_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("sheet", class_name="h-4 w-4 text-blue-600"),
                class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
            ),
            rx.el.div(
                rx.el.p(
                    "FREE",
                    class_name="text-sm font-semibold tracking-wide text-gray-900",
                ),
                rx.el.p(
                    "Everything you need to clean a spreadsheet and read the basics.",
                    class_name="text-xs font-medium text-gray-500 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.el.span(
                "\u20b90",
                class_name="text-4xl font-semibold text-gray-900",
            ),
            rx.el.span(
                "forever",
                class_name="text-sm font-medium text-gray-500 mb-1",
            ),
            class_name="flex items-end gap-2 mt-5",
        ),
        rx.el.ul(
            rx.foreach(FREE_FEATURES, _free_feature),
            class_name="flex flex-col gap-2.5 mt-5 pt-5 border-t border-gray-100",
        ),
        rx.el.button(
            rx.icon("cloud-upload", class_name="h-4 w-4"),
            "Start Free",
            on_click=PricingState.start_free,
            class_name="flex items-center justify-center gap-2 w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-100 transition-colors mt-6",
        ),
        rx.el.p(
            "No payment required — this takes you straight to the upload page.",
            class_name="text-xs font-medium text-gray-400 mt-3 text-center",
        ),
        class_name="flex flex-col w-full rounded-2xl border border-gray-200 bg-white p-6 shadow-sm",
    )


def _pro_notice() -> rx.Component:
    return rx.cond(
        PricingState.has_notice,
        rx.el.div(
            rx.icon(
                "circle-alert",
                class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
            ),
            rx.el.p(
                PricingState.notice,
                class_name="text-sm font-medium text-yellow-700",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-4 w-4"),
                on_click=PricingState.dismiss_notice,
                class_name="shrink-0 rounded-lg p-1 text-yellow-600 hover:bg-yellow-100 transition-colors",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3 mt-4",
        ),
    )


def _pro_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("sparkles", class_name="h-4 w-4 text-white"),
                    class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-indigo-600 shrink-0",
                ),
                rx.el.div(
                    rx.el.p(
                        "PRO",
                        class_name="text-sm font-semibold tracking-wide text-gray-900",
                    ),
                    rx.el.p(
                        "The full analytics engine — forecasting, segmentation and AI insights.",
                        class_name="text-xs font-medium text-gray-500 mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.span(
                rx.icon("star", class_name="h-3.5 w-3.5"),
                "Most popular",
                class_name="flex items-center gap-1.5 w-fit shrink-0 rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.span(
                "\u20b9199",
                class_name="text-4xl font-semibold text-indigo-600",
            ),
            rx.el.span(
                "/ month",
                class_name="text-sm font-medium text-gray-500 mb-1",
            ),
            class_name="flex items-end gap-2 mt-5",
        ),
        rx.el.ul(
            rx.foreach(PRO_FEATURES, _pro_feature),
            class_name="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-5 pt-5 border-t border-indigo-100",
        ),
        rx.el.button(
            rx.cond(
                PricingState.is_redirecting,
                rx.el.div(
                    class_name="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin"
                ),
                rx.icon("credit-card", class_name="h-4 w-4"),
            ),
            rx.el.span(PRO_BUTTON_LABEL),
            on_click=PricingState.upgrade_to_pro,
            disabled=PricingState.is_redirecting,
            class_name="flex items-center justify-center gap-2 w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors mt-6",
        ),
        _pro_notice(),
        rx.el.p(
            "Checkout opens on a secure external payment page configured by the InsightSheet team.",
            class_name="text-xs font-medium text-gray-400 mt-3 text-center",
        ),
        class_name="flex flex-col w-full rounded-2xl border-2 border-indigo-300 bg-white p-6 shadow-sm ring-4 ring-indigo-50",
    )


def _plans_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(_free_card(), class_name="w-full lg:flex-1 min-w-0"),
        rx.el.div(_pro_card(), class_name="w-full lg:flex-[1.15] min-w-0"),
        class_name="flex flex-col lg:flex-row items-stretch gap-6 w-full",
    )


def _faq_card(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item[0], class_name="h-4 w-4 text-blue-600"),
            class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.p(item[1], class_name="text-sm font-semibold text-gray-900"),
            rx.el.p(
                item[2], class_name="text-sm font-medium text-gray-500 mt-1"
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm w-full",
    )


def _faq_row() -> rx.Component:
    return rx.el.div(
        _faq_card(FAQ_ITEMS[0]),
        _faq_card(FAQ_ITEMS[1]),
        _faq_card(FAQ_ITEMS[2]),
        class_name="grid grid-cols-1 lg:grid-cols-3 gap-4 w-full",
    )


def _pricing_body() -> rx.Component:
    return rx.el.div(
        _intro(),
        _plans_row(),
        _faq_row(),
        class_name="flex flex-col gap-6 w-full",
    )


def pricing_page() -> rx.Component:
    return page_shell(
        "pricing",
        "Pricing / Upgrade",
        "Choose the plan that fits how deeply you analyse your data",
        _pricing_body(),
    )
