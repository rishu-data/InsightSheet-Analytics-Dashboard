import reflex as rx

from app.states.upload_state import UPLOAD_ID, UploadState


def _file_chip() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("file-spreadsheet", class_name="h-5 w-5 text-blue-600"),
            class_name="flex items-center justify-center h-10 w-10 rounded-lg bg-blue-50 shrink-0",
        ),
        rx.el.div(
            rx.el.p(
                UploadState.file_name,
                class_name="text-sm font-semibold text-gray-900 truncate",
            ),
            rx.el.p(
                f"{UploadState.file_size_kb} KB · {UploadState.clean_rows} clean rows · {UploadState.columns.length()} columns",
                class_name="text-xs font-medium text-gray-500",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-4 w-4"),
            on_click=UploadState.clear_file,
            class_name="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors",
        ),
        class_name="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3",
    )


def _demo_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                "No file handy?",
                class_name="text-sm font-semibold text-gray-900",
            ),
            rx.el.p(
                "Load a realistic 12-month sales export — complete with banner rows, duplicates and mixed date formats — to see the whole workflow.",
                class_name="text-sm font-medium text-gray-500 mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("flask-conical", class_name="h-4 w-4"),
            "Try demo dataset",
            on_click=UploadState.load_demo,
            disabled=UploadState.is_parsing,
            class_name="flex items-center gap-2 w-fit shrink-0 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-60 transition-colors",
        ),
        class_name="flex flex-wrap items-center justify-between gap-3 mt-4 rounded-xl border border-gray-200 bg-gray-50/60 p-4",
    )


def upload_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Upload your spreadsheet",
                    class_name="text-lg font-semibold text-gray-900",
                ),
                rx.el.p(
                    "CSV, XLS or XLSX. Messy exports are welcome — we clean them.",
                    class_name="text-sm font-medium text-gray-500",
                ),
            ),
            rx.el.span(
                rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                "Stays on this server",
                class_name="flex items-center gap-1.5 w-fit rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 mb-5",
        ),
        rx.upload.root(
            rx.el.div(
                rx.cond(
                    UploadState.is_parsing,
                    rx.el.div(
                        rx.el.div(
                            class_name="h-10 w-10 rounded-full border-2 border-blue-200 border-t-blue-600 animate-spin"
                        ),
                        rx.el.p(
                            "Reading and cleaning your file…",
                            class_name="text-sm font-semibold text-gray-700",
                        ),
                        class_name="flex flex-col items-center gap-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "cloud-upload",
                                class_name="h-6 w-6 text-blue-600",
                            ),
                            class_name="flex items-center justify-center h-12 w-12 rounded-xl bg-blue-50 mb-4",
                        ),
                        rx.el.p(
                            "Drag & drop your file here",
                            class_name="text-base font-semibold text-gray-900",
                        ),
                        rx.el.p(
                            "or click to browse — one file at a time, up to 10 MB",
                            class_name="text-sm font-medium text-gray-500 mt-1",
                        ),
                        rx.el.div(
                            rx.el.span(
                                ".csv",
                                class_name="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600",
                            ),
                            rx.el.span(
                                ".xlsx",
                                class_name="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600",
                            ),
                            rx.el.span(
                                ".xls",
                                class_name="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600",
                            ),
                            class_name="flex items-center gap-2 mt-4",
                        ),
                        class_name="flex flex-col items-center",
                    ),
                ),
                class_name="flex flex-col items-center justify-center px-6 py-12 rounded-xl border-2 border-dashed border-gray-300 bg-gray-50/60 hover:border-blue-400 hover:bg-blue-50/40 transition-colors cursor-pointer",
            ),
            id=UPLOAD_ID,
            accept={
                "text/csv": [".csv"],
                "application/vnd.ms-excel": [".xls"],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
                    ".xlsx"
                ],
            },
            multiple=False,
            max_files=1,
            max_size=10 * 1024 * 1024,
            on_drop=UploadState.handle_upload(
                rx.upload_files(upload_id=UPLOAD_ID)
            ),
            class_name="w-full",
        ),
        rx.cond(
            UploadState.error_message != "",
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-red-500 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    UploadState.error_message,
                    class_name="text-sm font-medium text-red-600",
                ),
                class_name="flex items-start gap-2 mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3",
            ),
        ),
        rx.cond(
            UploadState.warning_message != "",
            rx.el.div(
                rx.icon(
                    "circle-alert",
                    class_name="h-4 w-4 text-yellow-600 shrink-0 mt-0.5",
                ),
                rx.el.p(
                    UploadState.warning_message,
                    class_name="text-sm font-medium text-yellow-700",
                ),
                class_name="flex items-start gap-2 mt-4 rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3",
            ),
        ),
        rx.cond(
            UploadState.has_data, rx.el.div(_file_chip(), class_name="mt-4")
        ),
        _demo_row(),
        rx.el.div(
            rx.icon("lock", class_name="h-4 w-4 text-gray-400 shrink-0 mt-0.5"),
            rx.el.p(
                "Your spreadsheet is parsed in memory on this server for your session only. "
                "Nothing is stored on disk, shared, or sent to a third-party service.",
                class_name="text-sm font-medium text-gray-500",
            ),
            class_name="flex items-start gap-2 mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4",
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-6 w-full",
    )
