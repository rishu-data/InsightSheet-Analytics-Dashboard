import reflex as rx


def intro() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Turn a messy spreadsheet into clean, analysis-ready data",
            class_name="text-3xl sm:text-4xl font-semibold tracking-tight text-gray-900",
        ),
        rx.el.p(
            "Upload your sales export and InsightSheet finds the header row, drops blank and duplicate "
            "rows, standardises dates, and strips currency symbols — no formulas required.",
            class_name="text-base font-medium text-gray-500 mt-3 max-w-2xl",
        ),
        class_name="w-full",
    )


def how_it_works() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "How InsightSheet reads your file",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.div(
            _step(
                "search",
                "1. Find the real header",
                "We scan the first rows and skip export banners or logos above your column names.",
            ),
            _step(
                "eraser",
                "2. Tidy the rows",
                "Blank rows, spacer lines and exact duplicates are removed so counts are honest.",
            ),
            _step(
                "calendar-check",
                "3. Understand each column",
                "Dates in any format become YYYY-MM-DD; amounts lose $, £, commas and % signs.",
            ),
            _step(
                "check-check",
                "4. Confirm the meaning",
                "You map date, revenue, customer and product so the next step knows what to chart.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )


def _step(icon: str, title: str, detail: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
            class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-semibold text-gray-900"),
            rx.el.p(
                detail, class_name="text-sm font-medium text-gray-500 mt-0.5"
            ),
        ),
        class_name="flex items-start gap-3 rounded-xl border border-gray-100 bg-gray-50/60 p-4",
    )
