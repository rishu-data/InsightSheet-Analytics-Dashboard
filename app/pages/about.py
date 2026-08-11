import reflex as rx

from app.components.sidebar import page_shell


def _card(icon: str, title: str, body: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-blue-600"),
            class_name="flex items-center justify-center h-9 w-9 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-semibold text-gray-900"),
            rx.el.p(body, class_name="text-sm font-medium text-gray-500 mt-1"),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def _about_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Spreadsheet analytics without formulas",
                class_name="text-2xl font-semibold tracking-tight text-gray-900",
            ),
            rx.el.p(
                "InsightSheet takes a raw sales export, finds the real header row, removes blank and "
                "duplicate rows, standardises dates and strips currency symbols. Once you confirm what "
                "each column means, every figure on the dashboard is recalculated from those cleaned rows.",
                class_name="text-base font-medium text-gray-500 mt-3 max-w-3xl",
            ),
            class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
        ),
        rx.el.div(
            _card(
                "cloud-upload",
                "1. Upload",
                "CSV, XLS or XLSX up to 10 MB. Messy exports with banners and spacer rows are welcome.",
            ),
            _card(
                "wand-sparkles",
                "2. Clean",
                "Blank rows, duplicates and mixed date formats are handled automatically and logged in plain English.",
            ),
            _card(
                "columns-3",
                "3. Map",
                "Confirm the date, revenue, customer, product and order ID columns so the metrics know what they mean.",
            ),
            _card(
                "layout-dashboard",
                "4. Analyse",
                "Revenue trends, top customers and products, month-over-month change and customer inactivity.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-4 w-full",
        ),
        rx.el.div(
            rx.el.h3(
                "How the numbers are produced",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.ul(
                rx.el.li(
                    "Revenue is the sum of the mapped revenue column after currency symbols are removed.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                rx.el.li(
                    "Orders are the distinct values in the mapped Order ID column, or the cleaned rows with both a readable date and a numeric revenue value when no Order ID is mapped.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                rx.el.li(
                    "Average order value is total revenue divided by those orders.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                rx.el.li(
                    "Growth compares the latest month in the file with the month before it.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                rx.el.li(
                    "Inactivity counts days from the newest date in your file, flagging 60+ days without an order.",
                    class_name="text-sm font-medium text-gray-600",
                ),
                class_name="flex flex-col gap-2 mt-3 list-disc pl-5",
            ),
            rx.el.div(
                rx.icon(
                    "lock", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"
                ),
                rx.el.p(
                    "Files are processed on this server for your session only — nothing is shared or sent to a third party.",
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-gray-200 bg-gray-50 p-4 mt-5",
            ),
            class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
        ),
        class_name="flex flex-col gap-6 w-full",
    )


def about_page() -> rx.Component:
    return page_shell(
        "about",
        "About InsightSheet",
        "What happens to your spreadsheet and how metrics are calculated",
        _about_body(),
    )
