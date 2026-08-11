import reflex as rx

from app.states.upload_state import ROLES, UploadState


def _mapping_row(
    key: str, label: str, description: str, required: bool
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    label, class_name="text-sm font-semibold text-gray-900"
                ),
                rx.cond(
                    required,
                    rx.el.span(
                        "Required",
                        class_name="w-fit rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600",
                    ),
                    rx.el.span(
                        "Optional",
                        class_name="w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500",
                    ),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                description, class_name="text-xs font-medium text-gray-500 mt-1"
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Not mapped", value=""),
                rx.foreach(
                    UploadState.columns, lambda c: rx.el.option(c, value=c)
                ),
                value=UploadState.mapping[key],
                on_change=lambda v: UploadState.set_mapping(key, v),
                class_name="w-full appearance-none rounded-xl border border-gray-300 bg-white px-4 py-2.5 pr-10 text-sm font-medium text-gray-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-hidden transition-colors cursor-pointer",
            ),
            rx.icon(
                "chevron-down",
                class_name="h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
            ),
            class_name="relative w-full sm:w-64",
        ),
        class_name="flex flex-col sm:flex-row sm:items-center gap-3 py-4",
    )


def _derived_note(field: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "sparkles", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    field["name"],
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.span(
                    f"Used as {field['role']}",
                    class_name="w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                field["detail"],
                class_name="text-xs font-medium text-gray-500 mt-0.5",
            ),
            rx.el.p(
                f"Formula: {field['formula']} · {field['filled']} of rows filled",
                class_name="text-xs font-medium text-indigo-500 mt-1",
            ),
            class_name="min-w-0",
        ),
        class_name="flex items-start gap-2.5 rounded-xl border border-indigo-100 bg-white p-3",
    )


def _derived_banner() -> rx.Component:
    return rx.cond(
        UploadState.derived_fields.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.icon("wand-sparkles", class_name="h-4 w-4 text-indigo-600"),
                rx.el.p(
                    "Columns we built for you",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                UploadState.derived_summary,
                class_name="text-xs font-medium text-gray-500 mt-1",
            ),
            rx.el.div(
                rx.foreach(UploadState.derived_fields, _derived_note),
                class_name="flex flex-col gap-2 mt-3",
            ),
            class_name="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-4 mb-2",
        ),
    )


def _generate_footer() -> rx.Component:
    return rx.el.div(
        rx.cond(
            UploadState.mapping_error != "",
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    UploadState.mapping_error,
                    class_name="text-sm font-medium text-yellow-700",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3 mb-4",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    rx.cond(
                        UploadState.can_generate,
                        "Date and revenue are mapped — you're ready to go.",
                        "Date and revenue are required before metrics can be calculated.",
                    ),
                    class_name="text-sm font-medium text-gray-500",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("layout-dashboard", class_name="h-4 w-4"),
                "Generate dashboard",
                on_click=UploadState.generate_dashboard,
                class_name=rx.cond(
                    UploadState.can_generate,
                    "flex items-center gap-2 w-fit shrink-0 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors",
                    "flex items-center gap-2 w-fit shrink-0 rounded-xl bg-gray-200 px-4 py-2.5 text-sm font-semibold text-gray-500 hover:bg-gray-300 transition-colors",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        class_name="border-t border-gray-100 pt-5 mt-1",
    )


def mapping_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Confirm what each column means",
                class_name="text-lg font-semibold text-gray-900",
            ),
            rx.el.p(
                "We guessed based on your headers. Change anything that looks wrong.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="mb-2",
        ),
        _derived_banner(),
        rx.el.div(
            _mapping_row(ROLES[0][0], ROLES[0][1], ROLES[0][2], True),
            _mapping_row(ROLES[1][0], ROLES[1][1], ROLES[1][2], True),
            _mapping_row(ROLES[2][0], ROLES[2][1], ROLES[2][2], False),
            _mapping_row(ROLES[3][0], ROLES[3][1], ROLES[3][2], False),
            _mapping_row(ROLES[4][0], ROLES[4][1], ROLES[4][2], False),
            class_name="divide-y divide-gray-100",
        ),
        _generate_footer(),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )
