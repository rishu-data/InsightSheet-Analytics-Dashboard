import reflex as rx

from app.states.upload_state import ColumnInfo, UploadState


def _kind_badge(kind: rx.Var) -> rx.Component:
    return rx.el.span(
        kind,
        class_name=rx.match(
            kind,
            (
                "number",
                "w-fit rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600",
            ),
            (
                "date",
                "w-fit rounded-md bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-600",
            ),
            "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
        ),
    )


def _column_tile(col: ColumnInfo) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                col["name"],
                class_name="text-sm font-semibold text-gray-900 truncate",
            ),
            _kind_badge(col["kind"]),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.cond(
            col["derived"],
            rx.el.span(
                rx.icon("sparkles", class_name="h-3 w-3"),
                "Derived",
                class_name="flex items-center gap-1 w-fit rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-600 mt-2",
            ),
        ),
        rx.el.p(
            f"{col['filled']} filled",
            class_name="text-xs font-medium text-gray-500 mt-1",
        ),
        rx.cond(
            col["derived"],
            rx.el.p(
                col["source"],
                class_name="text-xs font-medium text-indigo-500 truncate mt-1",
            ),
        ),
        rx.el.p(
            col["sample"],
            class_name="text-xs font-medium text-gray-400 truncate mt-1",
        ),
        class_name=rx.cond(
            col["derived"],
            "w-full rounded-xl border border-indigo-200 bg-indigo-50/30 p-3",
            "w-full rounded-xl border border-gray-200 bg-white p-3",
        ),
    )


def column_overview_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Columns we detected",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                rx.cond(
                    UploadState.derived_fields.length() > 0,
                    "Type, completeness and a sample value for each column — derived columns are highlighted.",
                    "Type, completeness and a sample value for each column.",
                ),
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.foreach(UploadState.column_info, _column_tile),
            class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )


def _header_cell(name: rx.Var) -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon("table", class_name="h-3.5 w-3.5 text-gray-400"),
            rx.el.span(name),
            class_name="flex items-center gap-2",
        ),
        class_name="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap",
    )


def _row(row: rx.Var) -> rx.Component:
    return rx.el.tr(
        rx.foreach(
            UploadState.columns,
            lambda c: rx.el.td(
                row[c],
                class_name="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap",
            ),
        ),
        class_name="hover:bg-blue-50/40 even:bg-gray-50/60 transition-colors",
    )


def preview_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Cleaned data preview",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    f"First {UploadState.preview_rows.length()} of {UploadState.clean_rows} clean rows.",
                    class_name="text-sm font-medium text-gray-500",
                ),
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                "Start over",
                on_click=UploadState.clear_file,
                class_name="flex items-center gap-2 w-fit rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(rx.foreach(UploadState.columns, _header_cell)),
                        class_name="bg-gray-50 border-b border-gray-200",
                    ),
                    rx.el.tbody(
                        rx.foreach(UploadState.preview_rows, _row),
                        class_name="divide-y divide-gray-100",
                    ),
                    class_name="table-auto min-w-full",
                ),
                class_name="overflow-x-auto",
            ),
            class_name="rounded-xl border border-gray-200 overflow-hidden",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )
