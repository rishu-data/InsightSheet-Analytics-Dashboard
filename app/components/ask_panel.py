import reflex as rx

from app.states.ask_state import AskState, ChatTurn


def _suggestion_chip(question: rx.Var) -> rx.Component:
    return rx.el.button(
        rx.icon("sparkles", class_name="h-3.5 w-3.5 text-indigo-600 shrink-0"),
        rx.el.span(question, class_name="truncate"),
        on_click=lambda: AskState.ask(question),
        disabled=AskState.is_thinking,
        class_name="flex items-center gap-2 w-fit max-w-full rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-xs font-medium text-gray-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-60 transition-colors",
    )


def ask_header_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "circle-help",
                        class_name="h-5 w-5 text-indigo-600",
                    ),
                    class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-indigo-50 shrink-0",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Ask InsightSheet",
                        class_name="text-2xl font-semibold tracking-tight text-gray-900",
                    ),
                    rx.el.p(
                        "Ask questions about your business data in plain English.",
                        class_name="text-sm font-medium text-gray-500 mt-0.5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                    "Answers calculated from your rows only",
                    class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
                ),
                rx.cond(
                    AskState.has_turns,
                    rx.el.button(
                        rx.icon("eraser", class_name="h-4 w-4"),
                        "Clear",
                        on_click=AskState.clear_conversation,
                        class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5"
            ),
            rx.el.p(
                "Every answer is worked out from the cleaned rows currently in view, respecting your "
                "dashboard filters. Nothing is estimated or generated — if your dataset can't support "
                "an answer, I'll say so.",
                class_name="text-sm font-medium text-gray-600",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm w-full",
    )


def suggested_questions_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("list-checks", class_name="h-4 w-4 text-indigo-600"),
            rx.el.p(
                "Suggested questions",
                class_name="text-sm font-semibold text-gray-900",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            "Click one to ask it straight away.",
            class_name="text-xs font-medium text-gray-500 mt-0.5",
        ),
        rx.el.div(
            rx.foreach(AskState.suggestions, _suggestion_chip),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm w-full",
    )


def _evidence_item(item: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.icon(
            "circle-dot", class_name="h-3.5 w-3.5 text-indigo-600 shrink-0 mt-1"
        ),
        rx.el.span(item, class_name="text-sm font-medium text-gray-600"),
        class_name="flex items-start gap-2.5",
    )


def _question_bubble(question: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(question, class_name="text-sm font-medium text-white"),
            class_name="w-fit max-w-full rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5",
        ),
        class_name="flex justify-end w-full",
    )


def _answer_card(turn: ChatTurn) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(turn["answered"], "sheet", "circle-slash"),
                    class_name="h-4 w-4",
                ),
                class_name=rx.cond(
                    turn["answered"],
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 shrink-0",
                    "flex items-center justify-center h-8 w-8 rounded-lg bg-gray-100 text-gray-400 shrink-0",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    "Answer",
                    class_name=rx.cond(
                        turn["answered"],
                        "w-fit rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-600",
                        "w-fit rounded-md bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-500",
                    ),
                ),
                rx.el.p(
                    turn["answer"],
                    class_name=rx.cond(
                        turn["answered"],
                        "text-base font-semibold text-gray-900 mt-2",
                        "text-base font-semibold text-gray-600 mt-2",
                    ),
                ),
                class_name="min-w-0 flex flex-col items-start",
            ),
            class_name="flex items-start gap-3",
        ),
        rx.cond(
            turn["evidence"].length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search-check", class_name="h-3.5 w-3.5 text-gray-400"
                    ),
                    rx.el.span(
                        "Evidence",
                        class_name="text-xs font-semibold uppercase tracking-wide text-gray-500",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.ul(
                    rx.foreach(turn["evidence"], _evidence_item),
                    class_name="flex flex-col gap-2 mt-2.5",
                ),
                class_name="rounded-xl border border-gray-100 bg-gray-50/70 p-4 mt-4",
            ),
        ),
        rx.cond(
            turn["recommendation"] != "",
            rx.el.div(
                rx.icon(
                    "lightbulb",
                    class_name="h-4 w-4 text-indigo-600 shrink-0 mt-0.5",
                ),
                rx.el.div(
                    rx.el.span(
                        "Recommendation",
                        class_name="text-xs font-semibold uppercase tracking-wide text-indigo-600",
                    ),
                    rx.el.p(
                        turn["recommendation"],
                        class_name="text-sm font-medium text-gray-700 mt-1",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 mt-3",
            ),
        ),
        class_name="w-full rounded-2xl border border-gray-200 bg-white p-5 shadow-sm",
    )


def _turn_block(turn: ChatTurn) -> rx.Component:
    return rx.el.div(
        _question_bubble(turn["question"]),
        _answer_card(turn),
        class_name="flex flex-col gap-3 w-full",
    )


def _thinking_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-2 w-2 rounded-full bg-indigo-600 animate-pulse"
        ),
        rx.el.div(
            class_name="h-2 w-2 rounded-full bg-indigo-400 animate-pulse"
        ),
        rx.el.div(
            class_name="h-2 w-2 rounded-full bg-indigo-300 animate-pulse"
        ),
        rx.el.span(
            "Calculating from your rows…",
            class_name="text-sm font-medium text-gray-500 ml-2",
        ),
        class_name="flex items-center gap-1.5 w-fit rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm",
    )


def _transcript() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AskState.has_turns,
            rx.el.div(
                rx.foreach(AskState.turns, _turn_block),
                class_name="flex flex-col gap-6 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "message-square",
                        class_name="h-5 w-5 text-indigo-600",
                    ),
                    class_name="flex items-center justify-center h-11 w-11 rounded-xl bg-indigo-50 mb-3",
                ),
                rx.el.p(
                    "Nothing asked yet",
                    class_name="text-sm font-semibold text-gray-900",
                ),
                rx.el.p(
                    "Type a question below or pick a suggestion — answers arrive with the evidence behind them.",
                    class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-gray-50/60 px-6 py-12 w-full",
            ),
        ),
        rx.cond(AskState.is_thinking, _thinking_row()),
        class_name="flex flex-col gap-4 w-full",
    )


def _composer() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AskState.error_message != "",
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-red-500 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    AskState.error_message,
                    class_name="text-sm font-medium text-red-600",
                ),
                class_name="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 mb-3",
            ),
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    name="question",
                    placeholder="e.g. Which product sells best and is revenue growing?",
                    disabled=AskState.is_thinking,
                    class_name="w-full rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-800 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-hidden transition-colors disabled:bg-gray-50",
                ),
                rx.el.button(
                    rx.icon("send", class_name="h-4 w-4"),
                    rx.el.span("Ask", class_name="hidden sm:inline"),
                    type="submit",
                    disabled=AskState.is_thinking,
                    class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            on_submit=AskState.submit,
            reset_on_submit=True,
            class_name="w-full",
        ),
        rx.el.p(
            "No external AI is used. Answers are arithmetic over your uploaded rows, so they change when your filters change.",
            class_name="text-xs font-medium text-gray-400 mt-3",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm w-full",
    )


def ask_unavailable() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "circle-help",
                class_name="h-6 w-6 text-indigo-600",
            ),
            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-indigo-50 mb-4",
        ),
        rx.el.h2(
            "Nothing to ask about yet",
            class_name="text-lg font-semibold text-gray-900",
        ),
        rx.el.p(
            AskState.blocked_reason,
            class_name="text-sm font-medium text-gray-500 mt-1 max-w-md text-center",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("cloud-upload", class_name="h-4 w-4"),
                "Go to upload",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors",
            ),
            rx.el.a(
                rx.icon("columns-3", class_name="h-4 w-4"),
                "Adjust column mapping",
                href="/",
                class_name="flex items-center gap-2 w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors",
            ),
            class_name="flex flex-wrap items-center justify-center gap-3 mt-5",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white px-6 py-16 shadow-sm w-full",
    )


def _ask_body() -> rx.Component:
    return rx.el.div(
        suggested_questions_card(),
        _transcript(),
        _composer(),
        class_name="flex flex-col gap-4 w-full",
    )


def ask_section() -> rx.Component:
    return rx.el.div(
        ask_header_card(),
        rx.cond(AskState.ready, _ask_body(), ask_unavailable()),
        class_name="flex flex-col gap-6 w-full",
    )
