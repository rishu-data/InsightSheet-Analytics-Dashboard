import reflex as rx

_ACTIVE = "flex items-center gap-3 rounded-xl bg-blue-50 px-3 py-2.5 text-sm font-semibold text-blue-700 transition-colors"
_IDLE = "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
_PILL_ACTIVE = "flex items-center gap-2 shrink-0 w-fit rounded-full bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white"
_PILL_IDLE = "flex items-center gap-2 shrink-0 w-fit rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-xs font-medium text-gray-600 hover:border-blue-300 hover:text-blue-700 transition-colors"


def _nav_item(icon: str, label: str, href: str, active: bool) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        rx.el.span(label, class_name="truncate"),
        href=href,
        class_name=rx.cond(active, _ACTIVE, _IDLE),
    )


def _pill(icon: str, label: str, href: str, active: bool) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0"),
        rx.el.span(label),
        href=href,
        class_name=rx.cond(active, _PILL_ACTIVE, _PILL_IDLE),
    )


def _brand() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("sheet", class_name="h-4 w-4 text-white"),
            class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-600 shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                "InsightSheet",
                class_name="text-base font-semibold text-gray-900",
            ),
            rx.el.p(
                "Spreadsheet analytics",
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-center gap-2.5",
    )


def sidebar(active: str) -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            _brand(),
            class_name="flex items-center h-16 px-5 border-b border-gray-200",
        ),
        rx.el.nav(
            _nav_item(
                "cloud-upload", "Upload New File", "/", active == "upload"
            ),
            _nav_item(
                "layout-dashboard",
                "Dashboard",
                "/dashboard",
                active == "dashboard",
            ),
            _nav_item(
                "shield-check",
                "Data Quality",
                "/data-quality",
                active == "quality",
            ),
            _nav_item(
                "message-square-heart",
                "Feedback",
                "/feedback",
                active == "feedback",
            ),
            _nav_item(
                "credit-card",
                "Pricing / Upgrade",
                "/pricing",
                active == "pricing",
            ),
            _nav_item(
                "info", "About InsightSheet", "/about", active == "about"
            ),
            class_name="flex flex-col gap-1 w-full min-w-0 p-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "lock",
                    class_name="h-3.5 w-3.5 text-gray-400 mt-0.5 shrink-0",
                ),
                rx.el.p(
                    "Your file is processed on this server and never shared.",
                    class_name="text-xs font-medium text-gray-500",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3",
            ),
            class_name="mt-auto p-4",
        ),
        class_name="hidden lg:flex flex-col min-h-0 w-64 shrink-0 h-screen sticky top-0 border-r border-gray-200 bg-white",
    )


def _top_bar(active: str, title: str, subtitle: str) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    title,
                    class_name="text-lg font-semibold text-gray-900 truncate",
                ),
                rx.el.p(
                    subtitle,
                    class_name="text-xs font-medium text-gray-500 truncate",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(_brand(), class_name="lg:hidden"),
            class_name="flex items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 h-16",
        ),
        rx.el.div(
            _pill("cloud-upload", "Upload", "/", active == "upload"),
            _pill(
                "layout-dashboard",
                "Dashboard",
                "/dashboard",
                active == "dashboard",
            ),
            _pill(
                "shield-check",
                "Data Quality",
                "/data-quality",
                active == "quality",
            ),
            _pill(
                "message-square-heart",
                "Feedback",
                "/feedback",
                active == "feedback",
            ),
            _pill("credit-card", "Pricing", "/pricing", active == "pricing"),
            _pill("info", "About", "/about", active == "about"),
            class_name="lg:hidden flex items-center gap-2 overflow-x-auto px-4 sm:px-6 pb-3",
        ),
        class_name="w-full border-b border-gray-200 bg-white/85 backdrop-blur-sm sticky top-0 z-10",
    )


def page_shell(
    active: str, title: str, subtitle: str, content: rx.Component
) -> rx.Component:
    return rx.el.div(
        sidebar(active),
        rx.el.div(
            _top_bar(active, title, subtitle),
            rx.el.div(
                content,
                class_name="w-full px-4 sm:px-6 lg:px-8 py-8",
            ),
            class_name="flex-1 w-full min-w-0 flex flex-col",
        ),
        class_name="font-['Inter'] flex min-h-screen w-full bg-gray-50",
    )
