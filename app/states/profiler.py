"""Smart data profiler helpers.

Pure functions used by UploadState to describe a cleaned spreadsheet:
column level completeness, detected data types, invalid values, outliers,
automatically detected business columns and an overall quality score.
"""

from typing import TypedDict

import pandas as pd

BLANK_TOKENS: tuple[str, ...] = (
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "-",
    "--",
    "?",
    "unknown",
)

BOOLEAN_TOKENS: set[str] = {
    "yes",
    "no",
    "y",
    "n",
    "true",
    "false",
    "0",
    "1",
    "t",
    "f",
}


class ColumnProfile(TypedDict):
    name: str
    data_type: str
    kind: str
    role: str
    filled: int
    missing: int
    missing_pct: float
    missing_display: str
    complete_pct: int
    unique: int
    invalid: int
    outliers: int
    sample: str
    tone: str


class DatasetTotals(TypedDict):
    total_cells: int
    missing_cells: int
    typed_cells: int
    invalid_cells: int
    numeric_cells: int
    outlier_cells: int
    invalid_date_cells: int
    invalid_number_cells: int
    numeric_columns: int
    date_columns: int
    text_columns: int


class BusinessColumn(TypedDict):
    role: str
    column: str
    icon: str
    confidence: str
    detail: str


class CleaningOperation(TypedDict):
    icon: str
    title: str
    detail: str
    count: str
    applied: bool


class ScorePart(TypedDict):
    label: str
    detail: str
    points: float
    max_points: float
    pct: int
    icon: str


class TypeCount(TypedDict):
    label: str
    icon: str
    count: int


# role, icon, hints, why it matters
BUSINESS_ROLES: list[tuple[str, str, list[str], str]] = [
    (
        "Date",
        "calendar",
        [
            "order date",
            "invoice date",
            "sale date",
            "transaction date",
            "date",
            "created",
            "timestamp",
            "period",
            "day",
        ],
        "Drives every trend and month-over-month figure",
    ),
    (
        "Revenue",
        "dollar-sign",
        [
            "total revenue",
            "revenue",
            "total sales",
            "sales amount",
            "gross sales",
            "net sales",
            "line total",
            "total amount",
            "grand total",
            "turnover",
            "amount",
            "sales",
            "total",
        ],
        "Drives every money figure on the dashboard",
    ),
    (
        "Customer",
        "user-round",
        [
            "customer name",
            "customer",
            "client",
            "buyer",
            "account",
            "email",
            "user",
        ],
        "Used for retention and customer ranking",
    ),
    (
        "Product",
        "package",
        [
            "product category",
            "product name",
            "product",
            "category",
            "item",
            "sku",
            "service",
        ],
        "Used to rank what sells best",
    ),
    (
        "Order ID",
        "receipt",
        [
            "order id",
            "order no",
            "order number",
            "order #",
            "invoice",
            "transaction id",
            "receipt",
        ],
        "Used to count distinct orders",
    ),
    (
        "Quantity",
        "hash",
        ["units sold", "quantity sold", "quantity", "qty", "units", "volume"],
        "Volume sold on each line",
    ),
    (
        "Unit price",
        "tag",
        [
            "price per unit",
            "unit price",
            "price/unit",
            "selling price",
            "unit rate",
        ],
        "Price charged per unit",
    ),
    (
        "Cost",
        "receipt-text",
        [
            "cost of goods",
            "cost of sales",
            "total cost",
            "cogs",
            "unit cost",
            "cost",
            "expense",
        ],
        "Cost basis behind profit figures",
    ),
    (
        "Profit",
        "banknote",
        ["gross profit", "net profit", "total profit", "profit"],
        "Profit already present in your file",
    ),
    (
        "Discount",
        "percent",
        ["discount", "promo", "rebate", "markdown"],
        "Discounting applied per line",
    ),
    (
        "Region",
        "map-pin",
        [
            "region",
            "country",
            "state",
            "province",
            "city",
            "territory",
            "market",
            "zone",
        ],
        "Where the sale happened",
    ),
    (
        "Salesperson",
        "briefcase",
        [
            "salesperson",
            "sales rep",
            "sales person",
            "rep",
            "agent",
            "owner",
            "employee",
            "manager",
        ],
        "Who owned the sale",
    ),
]

NUMERIC_ROLES: set[str] = {
    "Revenue",
    "Quantity",
    "Unit price",
    "Cost",
    "Profit",
    "Discount",
}

TYPE_ICONS: dict[str, str] = {
    "Numeric": "hash",
    "Date": "calendar",
    "Categorical": "tags",
    "Identifier": "fingerprint",
    "Boolean": "toggle-left",
    "Text": "type",
    "Empty": "circle-slash",
}

TYPE_ORDER: list[str] = [
    "Numeric",
    "Date",
    "Categorical",
    "Identifier",
    "Boolean",
    "Text",
    "Empty",
]


def _norm(name: object) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[,$€£%\s]", "", regex=True),
        errors="coerce",
    )


def _blank_mask(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip().str.lower()
    return series.isna() | text.isin(BLANK_TOKENS)


def detect_business_columns(kinds: dict[str, str]) -> list[BusinessColumn]:
    """Match column names against known business concepts."""
    used: set[str] = set()
    found: list[BusinessColumn] = []
    for role, icon, hints, detail in BUSINESS_ROLES:
        match = ""
        confidence = "Medium"
        for hint in hints:
            for col in kinds:
                if col in used:
                    continue
                kind = kinds[col]
                if role in NUMERIC_ROLES and kind != "number":
                    continue
                if role == "Date" and kind != "date":
                    continue
                name = _norm(col)
                if name == hint:
                    match, confidence = col, "High"
                    break
                if hint in name and not match:
                    match, confidence = col, "Medium"
            if match and confidence == "High":
                break
        if match:
            used.add(match)
            found.append(
                BusinessColumn(
                    role=role,
                    column=match,
                    icon=icon,
                    confidence=confidence,
                    detail=detail,
                )
            )
    return found


def _data_type(series: pd.Series, kind: str, filled: int, unique: int) -> str:
    if filled == 0:
        return "Empty"
    if kind == "number":
        return "Numeric"
    if kind == "date":
        return "Date"
    values = set(
        series.dropna().astype(str).str.strip().str.lower().unique().tolist()
    )
    values.discard("")
    if values and values.issubset(BOOLEAN_TOKENS):
        return "Boolean"
    if filled >= 4 and unique == filled:
        return "Identifier"
    if unique <= max(2, min(30, int(filled * 0.3))):
        return "Categorical"
    return "Text"


def _tone(missing_pct: float, invalid: int, outliers: int) -> str:
    if missing_pct >= 40:
        return "bad"
    if missing_pct > 10 or invalid > 0:
        return "warn"
    if missing_pct > 0 or outliers > 0:
        return "info"
    return "good"


def _count_outliers(series: pd.Series) -> int:
    values = _numeric(series).dropna()
    if len(values) < 8:
        return 0
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    if iqr <= 0:
        return 0
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return int(((values < low) | (values > high)).sum())


def build_column_profiles(
    df: pd.DataFrame,
    kinds: dict[str, str],
    date_issues: dict[str, int],
    numeric_issues: dict[str, int],
    roles: dict[str, str],
) -> tuple[list[ColumnProfile], DatasetTotals]:
    rows = int(len(df))
    profiles: list[ColumnProfile] = []
    totals = DatasetTotals(
        total_cells=rows * int(len(df.columns)),
        missing_cells=0,
        typed_cells=0,
        invalid_cells=0,
        numeric_cells=0,
        outlier_cells=0,
        invalid_date_cells=0,
        invalid_number_cells=0,
        numeric_columns=0,
        date_columns=0,
        text_columns=0,
    )
    for col in df.columns:
        name = str(col)
        series = df[col]
        kind = kinds.get(name, "text")
        blanks = _blank_mask(series)
        missing = int(blanks.sum())
        filled = rows - missing
        unique = int(series[~blanks].astype(str).str.strip().nunique())
        missing_pct = round(missing / rows * 100, 1) if rows else 0.0
        invalid = 0
        outliers = 0
        if kind == "number":
            totals["numeric_columns"] += 1
            totals["numeric_cells"] += filled
            totals["typed_cells"] += filled
            invalid = int(numeric_issues.get(name, 0))
            totals["invalid_number_cells"] += invalid
            outliers = _count_outliers(series)
            totals["outlier_cells"] += outliers
        elif kind == "date":
            totals["date_columns"] += 1
            totals["typed_cells"] += filled
            invalid = int(date_issues.get(name, 0))
            totals["invalid_date_cells"] += invalid
        else:
            totals["text_columns"] += 1
        totals["missing_cells"] += missing
        totals["invalid_cells"] += invalid
        samples = series[~blanks].astype(str).str.strip().tolist()[:2]
        profiles.append(
            ColumnProfile(
                name=name,
                data_type=_data_type(series, kind, filled, unique),
                kind=kind,
                role=roles.get(name, ""),
                filled=filled,
                missing=missing,
                missing_pct=missing_pct,
                missing_display=f"{missing_pct:.1f}%",
                complete_pct=int(round(100 - missing_pct)),
                unique=unique,
                invalid=invalid,
                outliers=outliers,
                sample=", ".join(samples) if samples else "—",
                tone=_tone(missing_pct, invalid, outliers),
            )
        )
    return (profiles, totals)


def type_counts(profiles: list[ColumnProfile]) -> list[TypeCount]:
    tally: dict[str, int] = {}
    for profile in profiles:
        tally[profile["data_type"]] = tally.get(profile["data_type"], 0) + 1
    return [
        TypeCount(label=label, icon=TYPE_ICONS[label], count=tally[label])
        for label in TYPE_ORDER
        if tally.get(label)
    ]


def quality_band(score: int) -> tuple[str, str, str]:
    """Return (band, tone, plain-English meaning) for a 0-100 score."""
    if score >= 90:
        return (
            "Excellent",
            "good",
            "This file is analysis-ready — completeness, valid values and mapping all look strong.",
        )
    if score >= 75:
        return (
            "Good",
            "info",
            "Solid data. A few gaps or odd values exist, but every headline metric is trustworthy.",
        )
    if score >= 55:
        return (
            "Needs Attention",
            "warn",
            "Usable, but missing values, invalid entries or unmapped columns are affecting accuracy.",
        )
    return (
        "Poor",
        "bad",
        "Treat these numbers with care — large parts of the file are empty, unreadable or unmapped.",
    )
