import reflex as rx

from app.states.dashboard_state import DashboardState
from app.states.filter_state import FilterDimension, FilterState

_INPUT = (
    "w-full rounded-xl border border-gray-300 bg-white px-3.5 py-2.5 text-sm "
    "font-medium text-gray-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 "
    "outline-hidden transition-colors"
)
_SELECT = f"{_INPUT} appearance-none pr-10 cursor-pointer"


def _field_label(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-blue-600"),
        rx.el.span(label, class_name="text-xs font-semibold text-gray-600"),
        class_name="flex items-center gap-1.5",
    )


def _dimension_select(dim: FilterDimension) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field_label("filter", dim["label"]),
            rx.el.span(
                dim["column"],
                class_name="text-xs font-medium text-gray-400 truncate max-w-[120px]",
            ),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("All", value=""),
                rx.foreach(
                    dim["values"],
                    lambda value: rx.el.option(value, value=value),
                ),
                value=FilterState.selections[dim["key"]],
                on_change=lambda value: FilterState.select_dimension(
                    dim["key"], value
                ),
                class_name=_SELECT,
            ),
            rx.icon(
                "chevron-down",
                class_name="h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="w-full min-w-0",
    )


def _date_fields() -> rx.Component:
    return rx.cond(
        FilterState.date_available,
        rx.el.div(
            rx.el.div(
                _field_label("calendar", "From"),
                rx.el.input(
                    type="date",
                    default_value=FilterState.start_date,
                    min=FilterState.date_min,
                    max=FilterState.date_max,
                    on_change=FilterState.set_start.debounce(400),
                    class_name=f"{_INPUT} mt-1.5",
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                _field_label("calendar-check", "To"),
                rx.el.input(
                    type="date",
                    default_value=FilterState.end_date,
                    min=FilterState.date_min,
                    max=FilterState.date_max,
                    on_change=FilterState.set_end.debounce(400),
                    class_name=f"{_INPUT} mt-1.5",
                ),
                class_name="w-full min-w-0",
            ),
            class_name="contents",
        ),
    )


def _chip(label: rx.Var) -> rx.Component:
    return rx.el.span(
        rx.icon("check", class_name="h-3 w-3"),
        label,
        class_name="flex items-center gap-1.5 w-fit max-w-full rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 truncate",
    )


def clear_filters_button(primary: bool) -> rx.Component:
    return rx.el.button(
        rx.icon("filter-x", class_name="h-4 w-4"),
        "Clear filters",
        on_click=FilterState.reset_filters,
        class_name=rx.cond(
            primary,
            "flex items-center gap-2 w-fit rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors",
            "flex items-center gap-2 w-fit shrink-0 rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
        ),
    )


def filter_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "sliders-horizontal", class_name="h-4 w-4 text-blue-600"
                    ),
                    class_name="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Filters",
                        class_name="text-lg font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        FilterState.summary_line,
                        class_name="text-sm font-medium text-gray-500",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("rows-3", class_name="h-3.5 w-3.5"),
                    f"{DashboardState.filtered_rows} of {DashboardState.source_rows} rows",
                    class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
                ),
                rx.cond(
                    FilterState.has_active,
                    clear_filters_button(False),
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            _date_fields(),
            rx.foreach(FilterState.dimensions, _dimension_select),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mt-5",
        ),
        rx.cond(
            FilterState.has_active,
            rx.el.div(
                rx.el.span(
                    "Active:",
                    class_name="text-xs font-semibold text-gray-500",
                ),
                rx.foreach(FilterState.active_labels, _chip),
                class_name="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-gray-100",
            ),
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )
