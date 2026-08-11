import io
import logging
from typing import TypedDict

import pandas as pd
import reflex as rx

from app.states.profiler import (
    BusinessColumn,
    CleaningOperation,
    ColumnProfile,
    ScorePart,
    TypeCount,
    build_column_profiles,
    detect_business_columns,
    quality_band,
    type_counts,
)

UPLOAD_ID = "insightsheet_upload"

ROLES: list[tuple[str, str, str]] = [
    ("date", "Date", "When the sale or order happened"),
    ("revenue", "Revenue", "The money amount for each row"),
    ("customer", "Customer", "Who bought (name, email or ID)"),
    ("product", "Product / Category", "What was sold"),
    (
        "order_id",
        "Order ID",
        "Invoice or order reference, used to count orders",
    ),
]

REQUIRED_ROLES: list[str] = ["date", "revenue"]
EMPTY_MAPPING: dict[str, str] = {
    "date": "",
    "revenue": "",
    "customer": "",
    "product": "",
    "order_id": "",
}

DATE_HINTS = ["date", "day", "time", "created", "order date", "period", "month"]
REVENUE_HINTS = [
    "revenue",
    "amount",
    "total",
    "sales",
    "price",
    "value",
    "gross",
    "net",
]
CUSTOMER_HINTS = [
    "customer",
    "client",
    "buyer",
    "email",
    "account",
    "user",
    "name",
]
PRODUCT_HINTS = ["product", "item", "category", "sku", "service", "description"]
ORDER_HINTS = [
    "order id",
    "order_id",
    "order no",
    "order #",
    "invoice",
    "transaction",
    "receipt",
    "order",
    "id",
]

_BLANKS = ("", "nan", "none", "null", "n/a", "na", "-")

DERIVED_DATE_NAME = "Date (derived)"
DERIVED_REVENUE_NAME = "Total Revenue (derived)"

YEAR_NAMES: set[str] = {
    "year",
    "yr",
    "yyyy",
    "order year",
    "sale year",
    "sales year",
    "fiscal year",
    "transaction year",
}
MONTH_NAMES: set[str] = {
    "month",
    "mon",
    "mm",
    "month name",
    "month number",
    "month no",
    "order month",
    "sale month",
    "sales month",
    "transaction month",
}
DAY_NAMES: set[str] = {
    "day",
    "dd",
    "day number",
    "day of month",
    "order day",
    "sale day",
    "sales day",
    "transaction day",
}

UNITS_HINTS = [
    "units sold",
    "unit sold",
    "units ordered",
    "quantity sold",
    "quantity",
    "qty",
    "units",
    "volume",
]
PRICE_HINTS = [
    "price per unit",
    "price/unit",
    "unit price",
    "price per item",
    "selling price",
    "unit rate",
    "price",
    "rate",
]
STRICT_REVENUE_HINTS = [
    "total revenue",
    "revenue",
    "total sales",
    "sales amount",
    "gross sales",
    "net sales",
    "grand total",
    "line total",
    "total amount",
    "amount",
    "turnover",
    "total",
    "sales",
]
_NOT_REVENUE = ("per unit", "unit price", "price/unit", "per item", "units")

_MONTH_WORDS: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _month_number(value: object) -> float:
    """Turn a month cell (number or name) into 1-12, or NaN."""
    if value is None:
        return float("nan")
    text = str(value).strip().lower()
    if not text or text in _BLANKS:
        return float("nan")
    try:
        number = int(float(text.replace(",", "")))
        return float(number) if 1 <= number <= 12 else float("nan")
    except ValueError:
        pass
    key = text[:3]
    return float(_MONTH_WORDS[key]) if key in _MONTH_WORDS else float("nan")


def _numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[,$€£%\s]", "", regex=True),
        errors="coerce",
    )


class CleaningStep(TypedDict):
    icon: str
    title: str
    detail: str
    tone: str


class DerivedField(TypedDict):
    name: str
    role: str
    sources: str
    detail: str
    formula: str
    filled: str
    icon: str


class ColumnInfo(TypedDict):
    name: str
    kind: str
    filled: str
    sample: str
    derived: bool
    source: str


class UploadState(rx.State):
    file_name: str = ""
    file_size_kb: float = 0.0
    is_parsing: bool = False
    has_data: bool = False
    error_message: str = ""

    columns: list[str] = []
    column_info: list[ColumnInfo] = []
    derived_fields: list[DerivedField] = []
    preview_rows: list[dict[str, str]] = []
    clean_records: list[dict[str, str]] = []
    cleaning_log: list[CleaningStep] = []

    raw_rows: int = 0
    clean_rows: int = 0
    removed_blank_rows: int = 0
    removed_duplicates: int = 0
    parsed_dates: int = 0
    parsed_numbers: int = 0
    generated_headers: bool = False

    missing_values: int = 0
    date_issues: dict[str, int] = {}
    numeric_issues: dict[str, int] = {}
    auto_mapping: dict[str, str] = {}
    warning_message: str = ""
    mapping_error: str = ""
    is_demo: bool = False
    report_open: bool = True

    # Smart data profiler output
    column_profiles: list[ColumnProfile] = []
    business_columns: list[BusinessColumn] = []
    cleaning_operations: list[CleaningOperation] = []
    skipped_title_rows: int = 0
    trimmed_cells: int = 0
    total_cells: int = 0
    missing_cells: int = 0
    typed_cells: int = 0
    invalid_cells: int = 0
    numeric_cells: int = 0
    outlier_cells: int = 0
    invalid_date_cells: int = 0
    invalid_number_cells: int = 0
    numeric_columns: int = 0
    date_columns: int = 0
    text_columns: int = 0

    mapping: dict[str, str] = {
        "date": "",
        "revenue": "",
        "customer": "",
        "product": "",
        "order_id": "",
    }

    @rx.var
    def readiness(self) -> str:
        if not self.has_data:
            return "waiting"
        if self.mapping["date"] and self.mapping["revenue"]:
            return "ready"
        return "needs_mapping"

    @rx.var
    def readiness_title(self) -> str:
        return {
            "waiting": "Waiting for a file",
            "needs_mapping": "Almost there — confirm your columns",
            "ready": "Your data is ready for analysis",
        }[self.readiness]

    @rx.var
    def readiness_detail(self) -> str:
        if self.readiness == "waiting":
            return "Drop a CSV or Excel export of your sales and we'll tidy it up for you."
        if self.readiness == "needs_mapping":
            missing = []
            if not self.mapping["date"]:
                missing.append("a date column")
            if not self.mapping["revenue"]:
                missing.append("a revenue column")
            return f"We still need {' and '.join(missing)}. Pick the closest match below."
        return (
            f"{self.clean_rows} clean rows, dates and amounts understood. "
            "The dashboard step comes next."
        )

    def _ratio(self, good: float, total: float) -> float:
        if total <= 0:
            return 1.0
        return max(0.0, min(1.0, good / total))

    def _score_parts(self) -> list[ScorePart]:
        if not self.has_data or self.total_cells == 0:
            return []
        completeness = self._ratio(
            self.total_cells - self.missing_cells, self.total_cells
        )
        validity = self._ratio(
            self.typed_cells - self.invalid_cells, self.typed_cells
        )
        seen_rows = (
            self.clean_rows + self.removed_duplicates + self.removed_blank_rows
        )
        uniqueness = self._ratio(self.clean_rows, seen_rows)
        consistency = self._ratio(
            self.numeric_cells - self.outlier_cells, self.numeric_cells
        )
        mapped = (10.0 if self.mapping.get("date") else 0.0) + (
            10.0 if self.mapping.get("revenue") else 0.0
        )
        parts: list[ScorePart] = [
            ScorePart(
                label="Completeness",
                detail=f"{self.missing_cells:,} of {self.total_cells:,} cells are empty or unreadable",
                points=round(completeness * 30, 1),
                max_points=30.0,
                pct=int(round(completeness * 100)),
                icon="circle-slash",
            ),
            ScorePart(
                label="Validity",
                detail=f"{self.invalid_cells:,} of {self.typed_cells:,} typed values couldn't be read as a date or number",
                points=round(validity * 25, 1),
                max_points=25.0,
                pct=int(round(validity * 100)),
                icon="badge-check",
            ),
            ScorePart(
                label="Uniqueness",
                detail=f"{self.removed_duplicates:,} duplicate and {self.removed_blank_rows:,} blank row(s) were removed",
                points=round(uniqueness * 15, 1),
                max_points=15.0,
                pct=int(round(uniqueness * 100)),
                icon="copy",
            ),
            ScorePart(
                label="Consistency",
                detail=f"{self.outlier_cells:,} of {self.numeric_cells:,} numeric values sit far outside the normal range",
                points=round(consistency * 10, 1),
                max_points=10.0,
                pct=int(round(consistency * 100)),
                icon="scatter-chart",
            ),
            ScorePart(
                label="Mapping",
                detail=(
                    "Date and revenue columns are both mapped"
                    if mapped == 20.0
                    else "Map both a date and a revenue column to score full marks"
                ),
                points=mapped,
                max_points=20.0,
                pct=int(mapped / 20 * 100),
                icon="columns-3",
            ),
        ]
        return parts

    @rx.var
    def score_breakdown(self) -> list[ScorePart]:
        return self._score_parts()

    @rx.var
    def quality_score(self) -> int:
        parts = self._score_parts()
        if not parts:
            return 0
        return max(
            0, min(100, int(round(sum(part["points"] for part in parts))))
        )

    @rx.var
    def quality_band(self) -> str:
        return quality_band(self.quality_score)[0]

    @rx.var
    def quality_band_tone(self) -> str:
        return quality_band(self.quality_score)[1]

    @rx.var
    def quality_band_detail(self) -> str:
        if not self.has_data:
            return "Upload a spreadsheet to profile it."
        return quality_band(self.quality_score)[2]

    @rx.var
    def dataset_size_display(self) -> str:
        return f"{self.clean_rows:,} × {len(self.columns)}"

    @rx.var
    def missing_share_display(self) -> str:
        if self.total_cells == 0:
            return "0.0%"
        return f"{self.missing_cells / self.total_cells * 100:.1f}%"

    @rx.var
    def column_type_caption(self) -> str:
        return (
            f"{self.numeric_columns} numeric · {self.date_columns} date · "
            f"{self.text_columns} text"
        )

    @rx.var
    def type_summary(self) -> list[TypeCount]:
        return type_counts(self.column_profiles)

    @rx.var
    def operations_applied(self) -> int:
        return len([op for op in self.cleaning_operations if op["applied"]])

    @rx.var
    def can_generate(self) -> bool:
        return bool(
            self.has_data
            and self.mapping.get("date")
            and self.mapping.get("revenue")
        )

    @rx.var
    def invalid_dates(self) -> int:
        column = self.mapping.get("date", "")
        return int(self.date_issues.get(column, 0)) if column else 0

    @rx.var
    def invalid_revenue(self) -> int:
        column = self.mapping.get("revenue", "")
        return int(self.numeric_issues.get(column, 0)) if column else 0

    @rx.var
    def auto_detected(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for key, label, _detail in ROLES:
            column = self.auto_mapping.get(key, "")
            if column:
                rows.append({"role": label, "column": column})
        return rows

    @rx.var
    def needs_manual_mapping(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for key, label, detail in ROLES:
            if not self.mapping.get(key, ""):
                rows.append(
                    {
                        "role": label,
                        "detail": detail,
                        "requirement": (
                            "Required" if key in REQUIRED_ROLES else "Optional"
                        ),
                    }
                )
        return rows

    @rx.var
    def derived_names(self) -> list[str]:
        return [field["name"] for field in self.derived_fields]

    @rx.var
    def derived_summary(self) -> str:
        names = self.derived_names
        if not names:
            return ""
        if len(names) == 1:
            return f"We built “{names[0]}” from columns already in your file and pre-selected it below."
        joined = "” and “".join(names)
        return f"We built “{joined}” from columns already in your file and pre-selected them below."

    @rx.var
    def unmapped_columns(self) -> list[str]:
        used = {value for value in self.mapping.values() if value}
        return [c for c in self.columns if c not in used]

    @rx.var
    def source_label(self) -> str:
        if not self.has_data:
            return ""
        return "Demo dataset" if self.is_demo else self.file_name

    @rx.event
    def clear_file(self):
        self.file_name = ""
        self.file_size_kb = 0.0
        self.has_data = False
        self.error_message = ""
        self.columns = []
        self.column_info = []
        self.derived_fields = []
        self.preview_rows = []
        self.clean_records = []
        self.cleaning_log = []
        self.raw_rows = 0
        self.clean_rows = 0
        self.removed_blank_rows = 0
        self.removed_duplicates = 0
        self.parsed_dates = 0
        self.parsed_numbers = 0
        self.generated_headers = False
        self.missing_values = 0
        self.date_issues = {}
        self.numeric_issues = {}
        self.auto_mapping = {}
        self.warning_message = ""
        self.mapping_error = ""
        self.is_demo = False
        self.mapping = dict(EMPTY_MAPPING)
        self.column_profiles = []
        self.business_columns = []
        self.cleaning_operations = []
        self.skipped_title_rows = 0
        self.trimmed_cells = 0
        self.total_cells = 0
        self.missing_cells = 0
        self.typed_cells = 0
        self.invalid_cells = 0
        self.numeric_cells = 0
        self.outlier_cells = 0
        self.invalid_date_cells = 0
        self.invalid_number_cells = 0
        self.numeric_columns = 0
        self.date_columns = 0
        self.text_columns = 0

    @rx.event
    def set_mapping(self, role: str, column: str):
        self.mapping[role] = column
        self.mapping_error = ""

    @rx.event
    def toggle_report(self):
        self.report_open = not self.report_open

    @rx.event
    def generate_dashboard(self):
        from app.states.ask_state import AskState
        from app.states.dashboard_state import DashboardState
        from app.states.filter_state import FilterState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState
        from app.states.profit_state import ProfitState
        from app.states.report_state import ReportState
        from app.states.rfm_state import RFMState

        if not self.has_data:
            self.mapping_error = (
                "Upload a spreadsheet or load the demo dataset first."
            )
            return
        missing = [
            label
            for key, label, _d in ROLES
            if key in REQUIRED_ROLES and not self.mapping.get(key)
        ]
        if missing:
            self.mapping_error = f"Choose a column for {' and '.join(missing)} before generating the dashboard."
            return rx.toast(
                "Map the required columns first",
                duration=4000,
                close_button=True,
            )
        self.mapping_error = ""
        yield FilterState.build_filters
        yield DashboardState.compute_metrics
        yield ProfitState.compute_profit
        yield RFMState.compute_rfm
        yield InsightState.compute_insights
        yield ForecastState.compute_forecast
        yield AskState.prepare
        yield ReportState.prepare
        yield rx.redirect("/dashboard")

    @rx.event
    def load_demo(self):
        self.is_parsing = True
        self.error_message = ""
        self.mapping_error = ""
        yield
        self._load_demo()
        self.is_parsing = False

    @rx.event
    def load_demo_and_generate(self):
        from app.states.ask_state import AskState
        from app.states.dashboard_state import DashboardState
        from app.states.filter_state import FilterState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState
        from app.states.profit_state import ProfitState
        from app.states.report_state import ReportState
        from app.states.rfm_state import RFMState

        self.is_parsing = True
        self.error_message = ""
        self.mapping_error = ""
        yield
        loaded = self._load_demo()
        self.is_parsing = False
        if loaded:
            yield FilterState.build_filters
            yield DashboardState.compute_metrics
            yield ProfitState.compute_profit
            yield RFMState.compute_rfm
            yield InsightState.compute_insights
            yield ForecastState.compute_forecast
            yield AskState.prepare
            yield ReportState.prepare
            yield rx.redirect("/dashboard")

    def _load_demo(self) -> bool:
        from app.states.demo_data import demo_csv_bytes

        try:
            data = demo_csv_bytes()
            self.file_name = "demo_sales_export.csv"
            self.file_size_kb = round(len(data) / 1024, 1)
            self._parse_bytes(data, self.file_name)
            self.is_demo = True
            return True
        except Exception as e:
            logging.exception(f"Error loading demo dataset: {e}")
            self.has_data = False
            self.error_message = (
                "We couldn't build the demo dataset just now. Please try again."
            )
            return False

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        file = files[0]
        try:
            data = await file.read()
        except Exception as e:
            logging.exception(f"Error reading upload: {e}")
            self.error_message = (
                "We couldn't read that file. Please try uploading it again."
            )
            return
        if not file.name.lower().endswith((".csv", ".xls", ".xlsx")):
            self.error_message = (
                f"“{file.name}” isn't a spreadsheet we can read. "
                "Please export your data as .csv, .xls or .xlsx."
            )
            return
        if not data:
            self.error_message = (
                "That file was empty — there were no bytes to read."
            )
            return
        self.is_parsing = True
        self.error_message = ""
        self.mapping_error = ""
        self.is_demo = False
        self.file_name = file.name
        self.file_size_kb = round(len(data) / 1024, 1)
        yield
        try:
            self._parse_bytes(data, file.name)
        except ValueError as e:
            logging.exception(f"Unusable file uploaded: {e}")
            self.has_data = False
            self.error_message = str(e)
        except Exception as e:
            logging.exception(f"Error parsing file: {e}")
            self.has_data = False
            self.error_message = (
                "That file couldn't be read as a spreadsheet. "
                "Please upload a .csv, .xls or .xlsx export."
            )
        finally:
            self.is_parsing = False

    def _read_frame(self, data: bytes, name: str) -> pd.DataFrame:
        lower = name.lower()
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(data), header=None, dtype=object)
        text = data.decode("utf-8-sig", errors="replace")
        return pd.read_csv(
            io.StringIO(text),
            header=None,
            dtype=object,
            sep=None,
            engine="python",
            skip_blank_lines=True,
        )

    def _parse_bytes(self, data: bytes, name: str) -> None:
        raw = self._read_frame(data, name)
        raw = raw.dropna(axis=1, how="all")
        if raw.empty or len(raw.columns) == 0:
            raise ValueError(
                "That file looks empty — we couldn't find any rows of data inside it."
            )
        log: list[CleaningStep] = []

        header_row = self._find_header_row(raw)
        self.skipped_title_rows = int(header_row or 0)
        if header_row is None:
            self.generated_headers = True
            df = raw.copy()
            df.columns = [f"Column {i + 1}" for i in range(len(df.columns))]
            log.append(
                CleaningStep(
                    icon="table-properties",
                    title="No headers found",
                    detail="Your file started with data, so we named the columns for you. Rename them by mapping below.",
                    tone="amber",
                )
            )
        else:
            self.generated_headers = False
            header_values = raw.iloc[header_row].tolist()
            df = raw.iloc[header_row + 1 :].copy()
            df.columns = self._clean_headers(header_values)
            if header_row > 0:
                log.append(
                    CleaningStep(
                        icon="scissors",
                        title=f"Skipped {header_row} title row(s)",
                        detail="Export banners above the real header were removed.",
                        tone="blue",
                    )
                )

        self.raw_rows = int(len(df))

        before = len(df)
        df = df.dropna(axis=0, how="all")
        df = df.loc[
            ~df.apply(
                lambda r: all(str(v).strip() in ("", "nan", "None") for v in r),
                axis=1,
            )
        ]
        self.removed_blank_rows = int(before - len(df))
        if self.removed_blank_rows:
            log.append(
                CleaningStep(
                    icon="eraser",
                    title=f"Removed {self.removed_blank_rows} blank row(s)",
                    detail="Empty rows and spacer lines were dropped.",
                    tone="blue",
                )
            )

        before = len(df)
        df = df.drop_duplicates()
        self.removed_duplicates = int(before - len(df))
        if self.removed_duplicates:
            log.append(
                CleaningStep(
                    icon="copy",
                    title=f"Removed {self.removed_duplicates} duplicate row(s)",
                    detail="Identical rows were collapsed into one.",
                    tone="blue",
                )
            )

        df = df.reset_index(drop=True)
        trimmed = 0
        for col in df.columns:
            original = df[col]
            df[col] = original.map(
                lambda v: v.strip() if isinstance(v, str) else v
            )
            trimmed += int((original.astype(str) != df[col].astype(str)).sum())
        self.trimmed_cells = trimmed

        if len(df) == 0:
            raise ValueError(
                "Every row in that file was blank or a duplicate, so there was nothing left to analyse."
            )
        if len(df.columns) < 2:
            raise ValueError(
                "We only found a single column. Re-export your sheet so each field sits in its own column."
            )

        missing_cells = 0
        for col in df.columns:
            series = df[col]
            blanks = series.astype(str).str.strip().str.lower().isin(_BLANKS)
            missing_cells += int((series.isna() | blanks).sum())
        self.missing_values = missing_cells

        derived: list[DerivedField] = []
        date_field = self._derive_date_column(df)
        if date_field is not None:
            derived.append(date_field)
        revenue_field = self._derive_revenue_column(df)
        if revenue_field is not None:
            derived.append(revenue_field)
        self.derived_fields = derived
        derived_lookup = {field["name"]: field for field in derived}
        for field in derived:
            log.append(
                CleaningStep(
                    icon=field["icon"],
                    title=f"Created “{field['name']}”",
                    detail=field["detail"],
                    tone="green",
                )
            )

        date_issues: dict[str, int] = {}
        numeric_issues: dict[str, int] = {}
        info: list[ColumnInfo] = []
        date_cols: list[str] = []
        number_cols: list[str] = []
        for col in df.columns:
            series = df[col]
            kind = "text"
            numeric = pd.to_numeric(
                series.astype(str).str.replace(r"[,$€£%\s]", "", regex=True),
                errors="coerce",
            )
            dates = pd.to_datetime(
                series, errors="coerce", dayfirst=False, format="mixed"
            )
            non_null = int(series.notna().sum())
            date_issues[str(col)] = max(0, non_null - int(dates.notna().sum()))
            numeric_issues[str(col)] = max(
                0, non_null - int(numeric.notna().sum())
            )
            if non_null and numeric.notna().sum() >= max(
                1, int(non_null * 0.8)
            ):
                kind = "number"
                df[col] = numeric
                number_cols.append(col)
            elif non_null and dates.notna().sum() >= max(
                1, int(non_null * 0.7)
            ):
                kind = "date"
                df[col] = dates.dt.strftime("%Y-%m-%d")
                date_cols.append(col)
            filled = (
                0
                if len(df) == 0
                else int(round(df[col].notna().sum() / len(df) * 100))
            )
            sample_vals = df[col].dropna().astype(str).tolist()[:2]
            field = derived_lookup.get(col)
            info.append(
                ColumnInfo(
                    name=str(col),
                    kind=kind,
                    filled=f"{filled}%",
                    sample=", ".join(sample_vals) if sample_vals else "—",
                    derived=field is not None,
                    source=field["formula"] if field is not None else "",
                )
            )

        self.date_issues = date_issues
        self.numeric_issues = numeric_issues
        self.parsed_dates = len(date_cols)
        self.parsed_numbers = len(number_cols)
        if date_cols:
            log.append(
                CleaningStep(
                    icon="calendar-check",
                    title=f"Standardised {len(date_cols)} date column(s)",
                    detail=f"Mixed formats in {', '.join(date_cols)} were converted to YYYY-MM-DD.",
                    tone="green",
                )
            )
        if number_cols:
            log.append(
                CleaningStep(
                    icon="calculator",
                    title=f"Cleaned {len(number_cols)} numeric column(s)",
                    detail="Currency symbols, commas and percent signs were stripped so totals add up.",
                    tone="green",
                )
            )

        self.clean_rows = int(len(df))
        self.columns = [str(c) for c in df.columns]
        self.column_info = info
        preview = df.head(12).fillna("")
        self.preview_rows = [
            {str(k): str(v) for k, v in row.items()}
            for row in preview.to_dict(orient="records")
        ]
        self.clean_records = [
            {str(k): ("" if v is None else str(v)) for k, v in row.items()}
            for row in df.head(50000).fillna("").to_dict(orient="records")
        ]
        self.cleaning_log = log or [
            CleaningStep(
                icon="sparkles",
                title="Your file was already tidy",
                detail="No blank rows, duplicates or broken formats found.",
                tone="green",
            )
        ]
        guessed = {
            "date": self._guess(date_cols or self.columns, DATE_HINTS)
            or (date_cols[0] if date_cols else ""),
            "revenue": self._guess(number_cols or self.columns, REVENUE_HINTS)
            or (number_cols[0] if number_cols else ""),
            "customer": self._guess(self.columns, CUSTOMER_HINTS),
            "product": self._guess(self.columns, PRODUCT_HINTS),
            "order_id": self._guess(self.columns, ORDER_HINTS),
        }
        if DERIVED_DATE_NAME in self.columns:
            guessed["date"] = DERIVED_DATE_NAME
        if DERIVED_REVENUE_NAME in self.columns:
            guessed["revenue"] = DERIVED_REVENUE_NAME
        if guessed["order_id"] in (guessed["customer"], guessed["product"]):
            guessed["order_id"] = ""
        if guessed["product"] in (guessed["date"], guessed["revenue"]):
            guessed["product"] = ""
        self.auto_mapping = dict(guessed)
        self.mapping = dict(guessed)
        self.has_data = len(self.columns) > 0
        self._build_profile(
            df,
            {item["name"]: item["kind"] for item in info},
            date_issues,
            numeric_issues,
            date_cols,
            number_cols,
        )

        if not guessed["date"] and not guessed["revenue"]:
            self.warning_message = (
                "We couldn't recognise a date or an amount column in this file. "
                "Pick the closest matches below — if none fit, this export may not contain sales data."
            )
        elif not guessed["date"]:
            self.warning_message = "No date column was recognised. Choose the column that holds the order date below."
        elif not guessed["revenue"]:
            self.warning_message = "No revenue column was recognised. Choose the column that holds the amount below."
        else:
            self.warning_message = ""

    def _build_profile(
        self,
        df: pd.DataFrame,
        kinds: dict[str, str],
        date_issues: dict[str, int],
        numeric_issues: dict[str, int],
        date_cols: list[str],
        number_cols: list[str],
    ) -> None:
        """Profile the cleaned frame: types, gaps, invalid values and outliers."""
        business = detect_business_columns(kinds)
        self.business_columns = business
        roles = {item["column"]: item["role"] for item in business}
        profiles, totals = build_column_profiles(
            df, kinds, date_issues, numeric_issues, roles
        )
        self.column_profiles = profiles
        self.total_cells = totals["total_cells"]
        self.missing_cells = totals["missing_cells"]
        self.typed_cells = totals["typed_cells"]
        self.invalid_cells = totals["invalid_cells"]
        self.numeric_cells = totals["numeric_cells"]
        self.outlier_cells = totals["outlier_cells"]
        self.invalid_date_cells = totals["invalid_date_cells"]
        self.invalid_number_cells = totals["invalid_number_cells"]
        self.numeric_columns = totals["numeric_columns"]
        self.date_columns = totals["date_columns"]
        self.text_columns = totals["text_columns"]
        self.cleaning_operations = self._build_operations(
            date_cols, number_cols
        )

    def _build_operations(
        self, date_cols: list[str], number_cols: list[str]
    ) -> list[CleaningOperation]:
        derived = self.derived_names
        rows = max(1, self.clean_rows)
        return [
            CleaningOperation(
                icon="scissors",
                title="Header row detection",
                detail=(
                    "Export banners above your real column names were skipped."
                    if self.skipped_title_rows
                    else (
                        "No headers were found, so columns were named for you."
                        if self.generated_headers
                        else "Your header row was found on the first line."
                    )
                ),
                count=(
                    f"{self.skipped_title_rows} row(s) skipped"
                    if self.skipped_title_rows
                    else "Nothing skipped"
                ),
                applied=bool(self.skipped_title_rows or self.generated_headers),
            ),
            CleaningOperation(
                icon="eraser",
                title="Blank row removal",
                detail="Completely empty rows and spacer lines were dropped.",
                count=f"{self.removed_blank_rows} removed",
                applied=self.removed_blank_rows > 0,
            ),
            CleaningOperation(
                icon="copy",
                title="Duplicate row removal",
                detail="Rows identical across every column were collapsed into one.",
                count=f"{self.removed_duplicates} removed",
                applied=self.removed_duplicates > 0,
            ),
            CleaningOperation(
                icon="align-left",
                title="Whitespace trimming",
                detail="Leading and trailing spaces were stripped from text cells.",
                count=f"{self.trimmed_cells} cell(s) trimmed",
                applied=self.trimmed_cells > 0,
            ),
            CleaningOperation(
                icon="calendar-check",
                title="Date standardisation",
                detail=(
                    f"Mixed formats in {', '.join(date_cols)} were converted to YYYY-MM-DD."
                    if date_cols
                    else "No column looked like a date, so nothing was converted."
                ),
                count=f"{len(date_cols)} column(s)",
                applied=len(date_cols) > 0,
            ),
            CleaningOperation(
                icon="calculator",
                title="Numeric normalisation",
                detail=(
                    "Currency symbols, commas and percent signs were stripped so totals add up."
                    if number_cols
                    else "No numeric column was detected, so nothing was normalised."
                ),
                count=f"{len(number_cols)} column(s)",
                applied=len(number_cols) > 0,
            ),
            CleaningOperation(
                icon="wand-sparkles",
                title="Derived columns",
                detail=(
                    f"Built {', '.join(derived)} from values already present in your file."
                    if derived
                    else "Your file already contained the columns we needed."
                ),
                count=f"{len(derived)} created",
                applied=len(derived) > 0,
            ),
            CleaningOperation(
                icon="circle-slash",
                title="Missing value handling",
                detail="Empty cells are flagged, never invented — rows are only skipped where a metric needs that value.",
                count=f"{self.missing_cells} flagged",
                applied=self.missing_cells > 0,
            ),
            CleaningOperation(
                icon="scatter-chart",
                title="Outlier flagging",
                detail="Numeric values beyond 1.5 × IQR are highlighted but kept, so your totals stay true to the file.",
                count=f"{self.outlier_cells} flagged",
                applied=self.outlier_cells > 0,
            ),
            CleaningOperation(
                icon="list-checks",
                title="Valid record selection",
                detail=f"{self.clean_rows} of {self.raw_rows} rows survived cleaning and power every metric.",
                count=f"{int(self.clean_rows / rows * 100)}% kept",
                applied=True,
            ),
        ]

    def _clean_headers(self, values: list) -> list[str]:
        out: list[str] = []
        seen: dict[str, int] = {}
        for i, v in enumerate(values):
            name = (
                str(v).strip()
                if v is not None and str(v).strip() not in ("", "nan")
                else f"Column {i + 1}"
            )
            if name in seen:
                seen[name] += 1
                name = f"{name} ({seen[name]})"
            else:
                seen[name] = 1
            out.append(name)
        return out

    def _find_header_row(self, raw: pd.DataFrame) -> int | None:
        for idx in range(min(8, len(raw))):
            row = raw.iloc[idx].tolist()
            values = [
                str(v).strip()
                for v in row
                if v is not None and str(v).strip() not in ("", "nan")
            ]
            if len(values) < max(2, int(len(row) * 0.6)):
                continue
            texty = sum(1 for v in values if not self._looks_numeric(v))
            if texty >= max(2, int(len(values) * 0.7)):
                return idx
        return None

    def _looks_numeric(self, value: str) -> bool:
        try:
            float(value.replace(",", "").replace("$", "").replace("%", ""))
            return True
        except ValueError:
            return False

    def _guess(self, candidates: list[str], hints: list[str]) -> str:
        for hint in hints:
            for col in candidates:
                if hint in col.lower():
                    return col
        return ""

    def _exact_column(self, candidates: list[str], names: set[str]) -> str:
        for col in candidates:
            cleaned = str(col).strip().lower().replace("_", " ")
            cleaned = " ".join(cleaned.split())
            if cleaned in names:
                return str(col)
        return ""

    def _has_real_date_column(self, df: pd.DataFrame, skip: set[str]) -> bool:
        for col in df.columns:
            if str(col) in skip:
                continue
            text = df[col].astype(str).str.strip()
            sample = text[text.str.len() > 0]
            if sample.empty:
                continue
            if float(sample.str.contains(r"[-/]").mean()) < 0.7:
                continue
            try:
                parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            except Exception as e:
                logging.exception(f"Date probe failed for {col}: {e}")
                continue
            if float(parsed.notna().mean()) >= 0.7:
                return True
        return False

    def _has_real_revenue_column(self, df: pd.DataFrame) -> bool:
        for col in df.columns:
            name = str(col).strip().lower()
            if any(bad in name for bad in _NOT_REVENUE):
                continue
            if not any(hint in name for hint in STRICT_REVENUE_HINTS):
                continue
            series = df[col]
            non_null = int(series.notna().sum())
            if not non_null:
                continue
            numeric = _numeric_series(series)
            if int(numeric.notna().sum()) >= max(1, int(non_null * 0.8)):
                return True
        return False

    def _derive_date_column(self, df: pd.DataFrame) -> DerivedField | None:
        """Combine separate Year / Month / Day columns into one usable date."""
        columns = [str(c) for c in df.columns]
        if DERIVED_DATE_NAME in columns:
            return None
        year_col = self._exact_column(columns, YEAR_NAMES)
        month_col = self._exact_column(columns, MONTH_NAMES)
        if not year_col or not month_col or year_col == month_col:
            return None
        day_col = self._exact_column(columns, DAY_NAMES)
        if day_col in (year_col, month_col):
            day_col = ""
        skip = {year_col, month_col}
        if day_col:
            skip.add(day_col)
        if self._has_real_date_column(df, skip):
            return None

        years = pd.to_numeric(
            df[year_col].astype(str).str.replace(r"[^0-9\-]", "", regex=True),
            errors="coerce",
        )
        months = pd.to_numeric(
            df[month_col].map(_month_number), errors="coerce"
        )
        if day_col:
            days = pd.to_numeric(
                df[day_col].astype(str).str.replace(r"[^0-9]", "", regex=True),
                errors="coerce",
            ).fillna(1.0)
        else:
            days = pd.Series(1.0, index=df.index)

        frame = pd.DataFrame({"year": years, "month": months, "day": days})
        valid = (
            frame.notna().all(axis=1)
            & years.between(1000, 3000)
            & months.between(1, 12)
            & days.between(1, 31)
        )
        if not bool(valid.any()):
            return None
        stamps = pd.to_datetime(frame.loc[valid].astype(int), errors="coerce")
        series = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        series.loc[stamps.index] = stamps
        built = int(series.notna().sum())
        if built == 0:
            return None
        df[DERIVED_DATE_NAME] = series.dt.strftime("%Y-%m-%d")

        parts = [year_col, month_col] + ([day_col] if day_col else [])
        sources = ", ".join(parts)
        day_note = (
            ""
            if day_col
            else " No day column was found, so each row is dated on the 1st of its month."
        )
        percent = int(round(built / max(1, len(df)) * 100))
        return DerivedField(
            name=DERIVED_DATE_NAME,
            role="Date",
            sources=sources,
            detail=(
                f"Your file had no single date column, so we combined {sources} into "
                f"{DERIVED_DATE_NAME} (YYYY-MM-DD) for {built} row(s).{day_note}"
            ),
            formula=f"{sources} → YYYY-MM-DD",
            filled=f"{percent}%",
            icon="calendar-plus",
        )

    def _derive_revenue_column(self, df: pd.DataFrame) -> DerivedField | None:
        """Multiply units sold by price per unit when no revenue column exists."""
        columns = [str(c) for c in df.columns]
        if DERIVED_REVENUE_NAME in columns:
            return None
        if self._has_real_revenue_column(df):
            return None
        units_col = self._guess(columns, UNITS_HINTS)
        price_col = self._guess(columns, PRICE_HINTS)
        if not units_col or not price_col or units_col == price_col:
            return None
        units = _numeric_series(df[units_col])
        price = _numeric_series(df[price_col])
        product = (units * price).round(2)
        built = int(product.notna().sum())
        if built == 0:
            return None
        df[DERIVED_REVENUE_NAME] = product
        percent = int(round(built / max(1, len(df)) * 100))
        return DerivedField(
            name=DERIVED_REVENUE_NAME,
            role="Revenue",
            sources=f"{units_col}, {price_col}",
            detail=(
                f"No revenue column was present, so we multiplied {units_col} × {price_col} "
                f"to build {DERIVED_REVENUE_NAME} for {built} row(s)."
            ),
            formula=f"{units_col} × {price_col}",
            filled=f"{percent}%",
            icon="calculator",
        )
