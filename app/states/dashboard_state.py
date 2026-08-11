import logging
from typing import TypedDict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import reflex as rx

GRANULARITIES: list[str] = ["Daily", "Weekly", "Monthly"]
_RULES: dict[str, str] = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
_LABELS: dict[str, str] = {
    "Daily": "%b %d, %Y",
    "Weekly": "week of %b %d, %Y",
    "Monthly": "%b %Y",
}
INACTIVE_DAYS = 60
AT_RISK_DAYS = 30
ACCENT = "#4f46e5"
ACCENT_SOFT = "rgba(79, 70, 229, 0.12)"
GRID = "#eef2f7"


def money(value: float) -> str:
    return f"${value:,.2f}"


def _short(value: str, limit: int = 26) -> str:
    text = str(value).strip()
    if len(text) <= limit:
        return text or "(blank)"
    return f"{text[: limit - 1]}…"


def _col(mapping: dict[str, str] | None, key: str) -> str:
    """Read a mapped column name defensively (missing key, None, whitespace)."""
    if not isinstance(mapping, dict):
        return ""
    value = mapping.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert anything to a finite float, falling back to a default."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def _to_datetime(series: pd.Series) -> pd.Series:
    """Parse any column into tz-naive datetimes, never raising."""
    try:
        stamps = pd.to_datetime(series, errors="coerce", utc=True)
        return stamps.dt.tz_localize(None)
    except Exception as e:
        logging.exception(f"Date parsing fell back for a column: {e}")
    try:
        return pd.to_datetime(series, errors="coerce")
    except Exception as e:
        logging.exception(f"Date parsing failed for a column: {e}")
        return pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")


def _to_number(series: pd.Series) -> pd.Series:
    """Parse any column into floats, stripping currency noise, never raising."""
    try:
        return pd.to_numeric(
            series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True),
            errors="coerce",
        )
    except Exception as e:
        logging.exception(f"Numeric parsing failed for a column: {e}")
        return pd.Series(float("nan"), index=series.index, dtype="float64")


def _safe_div(numerator: float, denominator: float) -> float:
    """Divide without ever raising or returning NaN/inf."""
    top = _safe_float(numerator)
    bottom = _safe_float(denominator)
    if bottom == 0:
        return 0.0
    return _safe_float(top / bottom)


class MonthRow(TypedDict):
    period: str
    revenue: float
    revenue_display: str
    orders: int
    change: float
    change_display: str
    direction: str
    partial: bool


class CustomerRow(TypedDict):
    name: str
    last_order: str
    days_since: int
    orders: int
    revenue_display: str
    status: str


class InactivityBucket(TypedDict):
    key: str
    label: str
    icon: str
    customers: int
    revenue: float
    revenue_display: str
    share_display: str


class QualityCheck(TypedDict):
    key: str
    label: str
    detail: str
    flagged: bool


NOT_AVAILABLE = "Not available from this dataset."

INACTIVE_NOTE = (
    "This represents historical revenue associated with customers who have been "
    f"inactive for {INACTIVE_DAYS}+ days. It is not a prediction of future revenue loss."
)

LARGE_CHANGE_THRESHOLD = 30.0
LARGE_CHANGE_TITLE = "\u26a0\ufe0f Large Revenue Change Detected"
LARGE_CHANGE_MESSAGE = (
    "Verify data completeness before making business decisions."
)

_BUCKET_RANGES: list[tuple[str, str, str, int, int | None]] = [
    ("b1", "60\u201390 days", "hourglass", 60, 90),
    ("b2", "91\u2013180 days", "calendar-clock", 91, 180),
    ("b3", "181\u2013365 days", "calendar-x", 181, 365),
    ("b4", "365+ days", "archive", 366, None),
]


class KPI(TypedDict):
    key: str
    label: str
    icon: str
    value: str
    caption: str
    available: bool
    tone: str


class Highlight(TypedDict):
    key: str
    label: str
    value: str
    detail: str
    icon: str
    tone: str
    available: bool


def _blank_figure(message: str) -> go.Figure:
    fig = px.line()
    fig.update_layout(
        height=320,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "showarrow": False,
                "font": {"size": 13, "color": "#94a3b8"},
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
            }
        ],
    )
    return fig


class DashboardState(rx.State):
    granularity: str = "Monthly"
    has_metrics: bool = False
    blocked_reason: str = "Upload a spreadsheet to build your dashboard."
    source_name: str = ""

    total_revenue: float = 0.0
    total_revenue_display: str = "$0.00"
    order_count: int = 0
    order_caption: str = "Cleaned rows with date & revenue"
    has_order_data: bool = False
    customer_count: int = 0
    product_count: int = 0
    aov: float = 0.0
    aov_display: str = "$0.00"
    revenue_growth: float = 0.0
    growth_direction: str = "flat"
    growth_caption: str = "Not enough history yet"

    # Comparable-period growth (full month vs month-to-date)
    comparison_mode: str = "month"
    comparison_label: str = "Month-over-month growth"
    growth_metric_label: str = "Revenue growth %"
    latest_period_complete: bool = True
    mtd_days: int = 0
    mtd_current_display: str = "$0.00"
    mtd_previous_display: str = "$0.00"
    partial_month_note: str = ""

    # Large revenue change data-quality checks
    large_change_detected: bool = False
    large_change_anomaly: bool = False
    large_change_checks: list[QualityCheck] = []
    large_change_title: str = LARGE_CHANGE_TITLE
    large_change_message: str = LARGE_CHANGE_MESSAGE
    large_change_conclusion: str = ""

    period_start: str = ""
    period_end: str = ""
    summary_points: list[str] = []
    executive_highlights: list[Highlight] = []

    revenue_figure: go.Figure = _blank_figure("No revenue trend yet")
    customer_figure: go.Figure = _blank_figure("No customer column mapped")
    product_figure: go.Figure = _blank_figure("No product column mapped")
    best_period_label: str = ""
    best_period_display: str = ""
    trend_periods: int = 0

    month_history: list[MonthRow] = []
    latest_month: str = ""
    latest_revenue_display: str = "$0.00"
    latest_orders: int = 0
    latest_change: float = 0.0
    latest_direction: str = "flat"
    previous_month: str = ""

    customer_activity: list[CustomerRow] = []
    active_customers: int = 0
    at_risk_customers: int = 0
    inactive_customers: int = 0
    inactive_revenue_display: str = "$0.00"
    retention_rate: float = 0.0
    reference_date: str = ""
    inactive_note: str = INACTIVE_NOTE
    inactivity_buckets: list[InactivityBucket] = []

    # Customer concentration
    has_concentration: bool = False
    concentration_customers: int = 0
    top1_name: str = ""
    top1_share: float = 0.0
    top1_revenue_display: str = "$0.00"
    top5_count: int = 0
    top5_share: float = 0.0
    top5_revenue_display: str = "$0.00"
    top10_count: int = 0
    top10_share: float = 0.0
    top10_revenue_display: str = "$0.00"
    concentration_level: str = ""
    concentration_tone: str = "flat"
    concentration_detail: str = ""

    has_customer_data: bool = False
    has_product_data: bool = False

    # Filtering
    source_rows: int = 0
    filtered_rows: int = 0
    filters_applied: int = 0

    # Advanced KPI engine
    kpi_cards: list[KPI] = []
    has_growth: bool = False
    repeat_customers: int = 0
    repeat_rate: float = 0.0
    repeat_basis: str = ""
    revenue_per_customer: float = 0.0
    avg_orders_per_customer: float = 0.0
    avg_lifespan_months: float = 0.0
    months_observed: float = 0.0
    clv_estimate: float = 0.0
    clv_available: bool = False
    clv_caption: str = ""

    @rx.var
    def growth_display(self) -> str:
        sign = "+" if self.revenue_growth > 0 else ""
        return f"{sign}{self.revenue_growth:.1f}%"

    @rx.event
    def select_granularity(self, value: str):
        self.granularity = value
        return DashboardState.compute_metrics

    @rx.event
    async def compute_metrics(self):
        from app.states.filter_state import FilterState
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        self.source_name = upload.file_name
        quality: dict[str, int] = {
            "raw_rows": int(upload.raw_rows),
            "clean_rows": int(upload.clean_rows),
            "removed_duplicates": int(upload.removed_duplicates),
            "removed_blank_rows": int(upload.removed_blank_rows),
            "invalid_dates": int(upload.invalid_dates),
            "invalid_revenue": int(upload.invalid_revenue),
            "missing_values": int(upload.missing_values),
        }
        filters = await self.get_state(FilterState)
        selections = {
            key: value
            for key, value in (filters.selections or {}).items()
            if value
        }
        dim_columns = {
            str(dim["key"]): str(dim["column"])
            for dim in (filters.dimensions or [])
        }
        start = filters.start_date if filters.date_available else ""
        end = filters.end_date if filters.date_available else ""
        if not records:
            self._reset(
                "Upload a CSV or Excel export on the upload page and we'll build your dashboard from the cleaned rows."
            )
            return
        if not _col(mapping, "date") or not _col(mapping, "revenue"):
            self._reset(
                "Map a date column and a revenue column on the upload page to unlock the dashboard."
            )
            return
        try:
            self._build(
                records, mapping, selections, dim_columns, start, end, quality
            )
        except Exception as e:
            logging.exception(f"Error computing dashboard metrics: {e}")
            self._reset(
                "We couldn't calculate metrics from those columns. Try mapping a different date or revenue column."
            )

    def _reset(self, reason: str) -> None:
        self.has_metrics = False
        self.blocked_reason = reason
        self.total_revenue = 0.0
        self.total_revenue_display = "$0.00"
        self.order_count = 0
        self.order_caption = "Cleaned rows with date & revenue"
        self.has_order_data = False
        self.customer_count = 0
        self.product_count = 0
        self.aov = 0.0
        self.aov_display = "$0.00"
        self.revenue_growth = 0.0
        self.growth_direction = "flat"
        self.growth_caption = "Not enough history yet"
        self.period_start = ""
        self.period_end = ""
        self.summary_points = []
        self.executive_highlights = []
        self.revenue_figure = _blank_figure("No revenue trend yet")
        self.customer_figure = _blank_figure("No customer column mapped")
        self.product_figure = _blank_figure("No product column mapped")
        self.best_period_label = ""
        self.best_period_display = ""
        self.trend_periods = 0
        self.month_history = []
        self.latest_month = ""
        self.latest_revenue_display = "$0.00"
        self.latest_orders = 0
        self.latest_change = 0.0
        self.latest_direction = "flat"
        self.previous_month = ""
        self.customer_activity = []
        self.active_customers = 0
        self.at_risk_customers = 0
        self.inactive_customers = 0
        self.inactive_revenue_display = "$0.00"
        self.retention_rate = 0.0
        self.reference_date = ""
        self.has_customer_data = False
        self.has_product_data = False
        self.source_rows = 0
        self.filtered_rows = 0
        self.filters_applied = 0
        self.kpi_cards = []
        self.has_growth = False
        self.repeat_customers = 0
        self.repeat_rate = 0.0
        self.repeat_basis = ""
        self.revenue_per_customer = 0.0
        self.avg_orders_per_customer = 0.0
        self.avg_lifespan_months = 0.0
        self.months_observed = 0.0
        self.clv_estimate = 0.0
        self.clv_available = False
        self.clv_caption = ""
        self.comparison_mode = "month"
        self.comparison_label = "Month-over-month growth"
        self.growth_metric_label = "Revenue growth %"
        self.latest_period_complete = True
        self.mtd_days = 0
        self.mtd_current_display = "$0.00"
        self.mtd_previous_display = "$0.00"
        self.partial_month_note = ""
        self.large_change_detected = False
        self.large_change_anomaly = False
        self.large_change_checks = []
        self.large_change_conclusion = ""
        self.inactivity_buckets = []
        self._clear_concentration()

    def _clear_concentration(self) -> None:
        self.has_concentration = False
        self.concentration_customers = 0
        self.top1_name = ""
        self.top1_share = 0.0
        self.top1_revenue_display = "$0.00"
        self.top5_count = 0
        self.top5_share = 0.0
        self.top5_revenue_display = "$0.00"
        self.top10_count = 0
        self.top10_share = 0.0
        self.top10_revenue_display = "$0.00"
        self.concentration_level = ""
        self.concentration_tone = "flat"
        self.concentration_detail = (
            "Map a customer column on the upload page to measure how concentrated "
            "your revenue is."
        )

    def _build(
        self,
        records: list[dict[str, str]],
        mapping: dict[str, str],
        selections: dict[str, str] | None = None,
        dim_columns: dict[str, str] | None = None,
        start: str = "",
        end: str = "",
        quality: dict[str, int] | None = None,
    ) -> None:
        selections = selections if isinstance(selections, dict) else {}
        dim_columns = dim_columns if isinstance(dim_columns, dict) else {}
        start = str(start or "").strip()
        end = str(end or "").strip()
        if not records:
            self._reset(
                "Upload a CSV or Excel export on the upload page and we'll build your dashboard from the cleaned rows."
            )
            return
        date_col = _col(mapping, "date")
        rev_col = _col(mapping, "revenue")
        cust_col = _col(mapping, "customer")
        prod_col = _col(mapping, "product")
        order_col = _col(mapping, "order_id")
        if not date_col or not rev_col:
            self._reset(
                "Map a date column and a revenue column on the upload page to unlock the dashboard."
            )
            return

        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._reset(
                "There are no cleaned rows to calculate metrics from yet. Upload a spreadsheet on the upload page."
            )
            return
        if date_col not in df.columns or rev_col not in df.columns:
            self._reset(
                "The mapped columns are no longer in the cleaned file. Re-check your mapping on the upload page."
            )
            return

        df["_date"] = _to_datetime(df[date_col])
        df["_rev"] = _to_number(df[rev_col])
        df = df.dropna(subset=["_date", "_rev"])
        if df.empty:
            self._reset(
                "None of the rows had both a readable date and a numeric revenue value."
            )
            return

        source_rows = int(len(df))
        applied = 0
        start_stamp = pd.to_datetime(start, errors="coerce") if start else None
        end_stamp = pd.to_datetime(end, errors="coerce") if end else None
        if start_stamp is not None and not pd.isna(start_stamp):
            df = df[df["_date"] >= start_stamp]
            applied += 1
        if end_stamp is not None and not pd.isna(end_stamp):
            df = df[df["_date"] < end_stamp + pd.Timedelta(days=1)]
            applied += 1
        for key, value in selections.items():
            column = dim_columns.get(key, "")
            if not column or column not in df.columns:
                continue
            df = df[df[column].astype(str).str.strip() == value]
            applied += 1
        if df.empty:
            self._reset(
                "No rows match the filters you've chosen. Widen the date range or clear a filter to see metrics again."
            )
            self.source_rows = source_rows
            self.filtered_rows = 0
            self.filters_applied = applied
            return
        self.source_rows = source_rows
        self.filtered_rows = int(len(df))
        self.filters_applied = applied

        self.has_customer_data
        self.has_customer_data = bool(cust_col) and cust_col in df.columns
        self.has_product_data = bool(prod_col) and prod_col in df.columns

        self.has_order_data = bool(order_col) and order_col in df.columns
        total = _safe_float(df["_rev"].sum())
        orders = int(len(df))
        self.total_revenue = round(total, 2)
        self.total_revenue_display = money(total)
        if self.has_order_data:
            keys = df[order_col].astype(str).str.strip()
            distinct = int(keys[keys != ""].nunique())
            orders = distinct or orders
            self.order_caption = f"Distinct values in “{order_col}”"
        else:
            self.order_caption = "Cleaned rows with date & revenue"
        self.order_count = orders
        self.aov = round(_safe_div(total, orders), 2)
        self.aov_display = money(self.aov)
        self.period_start = df["_date"].min().strftime("%b %d, %Y")
        self.period_end = df["_date"].max().strftime("%b %d, %Y")

        if self.has_customer_data:
            cust_series = df[cust_col].astype(str).str.strip()
            cust_series = cust_series[cust_series.str.len() > 0]
            self.customer_count = int(cust_series.nunique())
        else:
            self.customer_count = 0

        if self.has_product_data:
            self.product_count = int(
                df[prod_col].astype(str).str.strip().nunique()
            )
        else:
            self.product_count = 0

        self._build_trend(df)
        self._build_month_history(df)
        top_customer = (
            self._build_rank_figure(df, cust_col, total, "customer")
            if self.has_customer_data
            else None
        )
        top_product = (
            self._build_rank_figure(df, prod_col, total, "product")
            if self.has_product_data
            else None
        )
        self._build_retention(df, cust_col, order_col)
        self._build_change_checks(quality if isinstance(quality, dict) else {})
        self._build_summary(top_customer, top_product)
        self._build_kpis()
        self.has_metrics = True
        self.blocked_reason = ""

    def _build_trend(self, df: pd.DataFrame) -> None:
        rule = _RULES.get(self.granularity, "MS")
        series = df.set_index("_date")["_rev"].resample(rule).sum()
        frame = pd.DataFrame(
            {"Period": series.index, "Revenue": series.to_numpy(dtype=float)}
        )
        self.trend_periods = int(len(frame))
        fig = px.line(frame, x="Period", y="Revenue", markers=True)
        fig.update_traces(
            line={"color": ACCENT, "width": 2.5},
            marker={"size": 6, "color": ACCENT},
            fill="tozeroy",
            fillcolor=ACCENT_SOFT,
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.2f}<extra></extra>",
        )
        fig.update_layout(
            height=340,
            autosize=True,
            margin={"l": 50, "r": 20, "t": 20, "b": 45},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            hovermode="x unified",
            showlegend=False,
        )
        fig.update_xaxes(
            title_text="",
            showgrid=False,
            linecolor=GRID,
            ticks="outside",
            tickcolor=GRID,
        )
        fig.update_yaxes(
            title_text="Revenue",
            gridcolor=GRID,
            zerolinecolor=GRID,
            tickprefix="$",
        )
        self.revenue_figure = fig

        if not frame.empty and bool(frame["Revenue"].notna().any()):
            best = frame.loc[frame["Revenue"].idxmax()]
            fmt = _LABELS.get(self.granularity, "%b %Y")
            self.best_period_label = pd.Timestamp(best["Period"]).strftime(fmt)
            self.best_period_display = money(_safe_float(best["Revenue"]))
        else:
            self.best_period_label = ""
            self.best_period_display = ""

    def _build_month_history(self, df: pd.DataFrame) -> None:
        monthly = (
            df.set_index("_date")["_rev"]
            .resample("MS")
            .agg(["sum", "size"])
            .rename(columns={"sum": "revenue", "size": "orders"})
        )
        last_date = df["_date"].max()
        stamps = [pd.Timestamp(index) for index in monthly.index]
        final_end = (
            (stamps[-1] + pd.offsets.MonthEnd(0)).normalize()
            if stamps
            else None
        )
        self.latest_period_complete = bool(
            final_end is None or last_date.normalize() >= final_end
        )
        total_months = len(stamps)
        rows: list[MonthRow] = []
        prev_value: float | None = None
        for position, (stamp, row) in enumerate(monthly.iterrows()):
            revenue = _safe_float(row["revenue"])
            change = 0.0
            direction = "flat"
            has_prev = prev_value is not None and prev_value > 0
            if has_prev and prev_value:
                change = _safe_div(revenue - prev_value, prev_value) * 100
                direction = (
                    "up" if change > 0 else ("down" if change < 0 else "flat")
                )
            rows.append(
                MonthRow(
                    period=pd.Timestamp(stamp).strftime("%b %Y"),
                    revenue=round(revenue, 2),
                    revenue_display=money(revenue),
                    orders=int(row["orders"]),
                    change=round(change, 1),
                    change_display=(
                        f"{'+' if change > 0 else ''}{change:.1f}%"
                        if has_prev
                        else "\u2014"
                    ),
                    direction=direction,
                    partial=bool(
                        position == total_months - 1
                        and not self.latest_period_complete
                    ),
                )
            )
            prev_value = revenue

        self.month_history = list(reversed(rows[-12:]))
        if not rows:
            self.latest_month = ""
            self.previous_month = ""
            self.growth_caption = "Not enough history yet"
            self.has_growth = False
            self.partial_month_note = ""
            self.comparison_mode = "month"
            self.comparison_label = "Month-over-month growth"
            self.growth_metric_label = "Revenue growth %"
            return

        latest = rows[-1]
        self.latest_month = latest["period"]
        self.latest_revenue_display = latest["revenue_display"]
        self.latest_orders = latest["orders"]
        self.latest_change = latest["change"]
        self.latest_direction = latest["direction"]
        self.previous_month = rows[-2]["period"] if len(rows) > 1 else ""

        if len(rows) < 2:
            self.revenue_growth = 0.0
            self.growth_direction = "flat"
            self.comparison_mode = "month"
            self.comparison_label = "Month-over-month growth"
            self.growth_metric_label = "Revenue growth %"
            self.growth_caption = "Only one month of data in this range"
            self.has_growth = False
            self.mtd_days = 0
            self.mtd_current_display = "$0.00"
            self.mtd_previous_display = "$0.00"
            self.partial_month_note = (
                f"{latest['period']} is still in progress — data ends "
                f"{last_date.strftime('%b %d, %Y')}."
                if not self.latest_period_complete
                else ""
            )
            return

        if self.latest_period_complete:
            self.comparison_mode = "month"
            self.comparison_label = "Month-over-month growth"
            self.growth_metric_label = "Revenue growth %"
            self.revenue_growth = latest["change"]
            self.growth_direction = latest["direction"]
            self.growth_caption = (
                f"{latest['period']} vs {self.previous_month} "
                "(complete months compared)"
            )
            self.mtd_days = 0
            self.mtd_current_display = "$0.00"
            self.mtd_previous_display = "$0.00"
            self.partial_month_note = ""
        else:
            self._month_to_date(
                df, latest["period"], self.previous_month, last_date
            )
        self.has_growth = True

    def _month_to_date(
        self,
        df: pd.DataFrame,
        latest_label: str,
        previous_label: str,
        last_date: pd.Timestamp,
    ) -> None:
        """Compare equal month-to-date windows when the latest month is partial."""
        day = int(last_date.day)
        current_start = last_date.normalize().replace(day=1)
        previous_start = (current_start - pd.DateOffset(months=1)).normalize()
        previous_days = int(pd.Timestamp(previous_start).days_in_month)
        window = max(1, min(day, previous_days))
        previous_end = previous_start + pd.Timedelta(days=window - 1)
        current = _safe_float(
            df[(df["_date"] >= current_start) & (df["_date"] <= last_date)][
                "_rev"
            ].sum()
        )
        previous = _safe_float(
            df[
                (df["_date"] >= previous_start)
                & (df["_date"] < previous_end + pd.Timedelta(days=1))
            ]["_rev"].sum()
        )
        change = _safe_div(current - previous, abs(previous)) * 100
        self.comparison_mode = "mtd"
        self.comparison_label = "Month-to-Date growth"
        self.growth_metric_label = "Month-to-Date growth %"
        self.revenue_growth = round(change, 1)
        self.growth_direction = (
            "up" if change > 0 else ("down" if change < 0 else "flat")
        )
        self.mtd_days = window
        self.mtd_current_display = money(current)
        self.mtd_previous_display = money(previous)
        self.growth_caption = (
            f"Month-to-date: {latest_label} days 1\u2013{window} "
            f"({money(current)}) vs {previous_label} days 1\u2013{window} "
            f"({money(previous)})"
        )
        self.partial_month_note = (
            f"{latest_label} is still in progress — data ends "
            f"{last_date.strftime('%b %d, %Y')}. To keep the comparison fair we "
            f"compare the first {window} day(s) of {latest_label} with the first "
            f"{window} day(s) of {previous_label} rather than a partial month "
            "against a complete one."
        )

    def _build_change_checks(self, quality: dict[str, int]) -> None:
        """Run basic data-quality checks behind a large comparable-period change."""
        change = abs(_safe_float(self.revenue_growth))
        if not self.has_growth or change <= LARGE_CHANGE_THRESHOLD:
            self.large_change_detected = False
            self.large_change_anomaly = False
            self.large_change_checks = []
            self.large_change_conclusion = ""
            return

        raw_rows = max(0, int(quality.get("raw_rows", 0) or 0))
        clean_rows = max(0, int(quality.get("clean_rows", 0) or 0))
        duplicates = max(0, int(quality.get("removed_duplicates", 0) or 0))
        blanks = max(0, int(quality.get("removed_blank_rows", 0) or 0))
        invalid_dates = max(0, int(quality.get("invalid_dates", 0) or 0))
        invalid_revenue = max(0, int(quality.get("invalid_revenue", 0) or 0))
        removed = max(0, raw_rows - clean_rows)
        removed_share = _safe_div(removed, raw_rows) * 100
        duplicate_share = _safe_div(duplicates, raw_rows) * 100
        date_share = _safe_div(invalid_dates, max(1, raw_rows)) * 100
        revenue_share = _safe_div(invalid_revenue, max(1, raw_rows)) * 100

        checks: list[QualityCheck] = [
            QualityCheck(
                key="records",
                label="Number of records analysed",
                detail=(
                    f"{self.filtered_rows:,} row(s) of {self.source_rows:,} are in view. "
                    + (
                        "That is a small sample, so a single order can move the percentage a long way."
                        if self.filtered_rows < 30
                        else "That is enough rows for the percentage to be meaningful."
                    )
                ),
                flagged=self.filtered_rows < 30,
            ),
            QualityCheck(
                key="dates",
                label="Missing or unreadable dates",
                detail=(
                    f"{invalid_dates:,} cell(s) in the mapped date column could not be read "
                    f"({date_share:.1f}% of the rows in the file)."
                    if invalid_dates
                    else "Every row in the mapped date column held a readable date."
                ),
                flagged=date_share > 2.0,
            ),
            QualityCheck(
                key="revenue",
                label="Missing or unreadable revenue values",
                detail=(
                    f"{invalid_revenue:,} cell(s) in the mapped revenue column could not be read "
                    f"({revenue_share:.1f}% of the rows in the file)."
                    if invalid_revenue
                    else "Every row in the mapped revenue column held a numeric amount."
                ),
                flagged=revenue_share > 2.0,
            ),
            QualityCheck(
                key="duplicates",
                label="Duplicate records",
                detail=(
                    f"{duplicates:,} identical row(s) were removed during cleaning "
                    f"({duplicate_share:.1f}% of the file)."
                    if duplicates
                    else "No duplicate rows were found in your export."
                ),
                flagged=duplicate_share > 5.0,
            ),
            QualityCheck(
                key="period",
                label="Is the current period complete?",
                detail=(
                    f"{self.latest_month} is still in progress, so equal month-to-date "
                    f"windows (first {self.mtd_days} day(s)) are being compared."
                    if not self.latest_period_complete
                    else f"{self.latest_month} is a complete month, so full months are compared."
                ),
                flagged=not self.latest_period_complete,
            ),
            QualityCheck(
                key="cleaning",
                label="Data removed during cleaning",
                detail=(
                    f"{removed:,} of {raw_rows:,} row(s) were removed "
                    f"({removed_share:.1f}%) \u2014 {duplicates:,} duplicate(s) and "
                    f"{blanks:,} blank row(s)."
                    if raw_rows
                    else "No cleaning statistics are available for this dataset."
                ),
                flagged=removed_share > 20.0,
            ),
        ]

        self.large_change_checks = checks
        self.large_change_detected = True
        self.large_change_anomaly = any(check["flagged"] for check in checks)
        if self.large_change_anomaly:
            self.large_change_conclusion = (
                f"{self.comparison_label} of {self.growth_display} is larger than "
                f"{LARGE_CHANGE_THRESHOLD:.0f}%, and the checks above flagged something "
                "worth confirming before you act on it. This does not prove the change "
                "is caused by data issues \u2014 review the flagged item(s) and your own "
                "records first."
            )
        else:
            self.large_change_conclusion = (
                f"{self.comparison_label} of {self.growth_display} is larger than "
                f"{LARGE_CHANGE_THRESHOLD:.0f}%, but none of the checks above found a "
                "data-quality problem, so the movement appears to come from your actual "
                "sales rather than missing or duplicated rows."
            )

    def _build_buckets(self, inactive: pd.DataFrame) -> None:
        """Split 60+ day inactive customers into day-range buckets."""
        if inactive.empty:
            self.inactivity_buckets = []
            return
        total = _safe_float(inactive["revenue"].sum())
        buckets: list[InactivityBucket] = []
        for key, label, icon, low, high in _BUCKET_RANGES:
            if high is None:
                block = inactive[inactive["days_since"] >= low]
            else:
                block = inactive[
                    (inactive["days_since"] >= low)
                    & (inactive["days_since"] <= high)
                ]
            revenue = _safe_float(block["revenue"].sum())
            buckets.append(
                InactivityBucket(
                    key=key,
                    label=label,
                    icon=icon,
                    customers=int(len(block)),
                    revenue=round(revenue, 2),
                    revenue_display=money(revenue),
                    share_display=f"{_safe_div(revenue, total) * 100:.1f}%",
                )
            )
        self.inactivity_buckets = buckets

    def _build_concentration(self, grouped: pd.DataFrame) -> None:
        """Measure how much revenue sits with the largest customers."""
        ranked = grouped.sort_values("revenue", ascending=False)
        total = _safe_float(ranked["revenue"].sum())
        count = int(len(ranked))
        if count == 0 or total <= 0:
            self._clear_concentration()
            return
        top1 = _safe_float(ranked["revenue"].iloc[0])
        top5_count = min(5, count)
        top10_count = min(10, count)
        top5 = _safe_float(ranked["revenue"].head(top5_count).sum())
        top10 = _safe_float(ranked["revenue"].head(top10_count).sum())
        self.concentration_customers = count
        self.top1_name = _short(ranked.index[0], 32)
        self.top1_share = round(_safe_div(top1, total) * 100, 1)
        self.top1_revenue_display = money(top1)
        self.top5_count = top5_count
        self.top5_share = round(_safe_div(top5, total) * 100, 1)
        self.top5_revenue_display = money(top5)
        self.top10_count = top10_count
        self.top10_share = round(_safe_div(top10, total) * 100, 1)
        self.top10_revenue_display = money(top10)
        if self.top1_share >= 30 or self.top5_share >= 60:
            self.concentration_level = "High concentration"
            self.concentration_tone = "down"
            self.concentration_detail = (
                f"Your top {top5_count} customer(s) generate {self.top5_share:.1f}% of "
                f"revenue across {count:,} customer(s). Losing one of them would move the "
                "whole business, so retention of those accounts matters most."
            )
        elif self.top1_share >= 15 or self.top5_share >= 35:
            self.concentration_level = "Moderate concentration"
            self.concentration_tone = "flat"
            self.concentration_detail = (
                f"Your top {top5_count} customer(s) generate {self.top5_share:.1f}% of "
                f"revenue across {count:,} customer(s). The base is reasonably spread, but a "
                "few accounts still carry noticeable weight."
            )
        else:
            self.concentration_level = "Low concentration"
            self.concentration_tone = "up"
            self.concentration_detail = (
                f"Your top {top5_count} customer(s) generate only {self.top5_share:.1f}% of "
                f"revenue across {count:,} customer(s), so revenue is well spread and no "
                "single account dominates."
            )
        self.has_concentration = True

    def _build_rank_figure(
        self, df: pd.DataFrame, column: str, total: float, kind: str
    ) -> tuple[str, float] | None:
        grouped = (
            df.assign(
                _key=df[column].astype(str).str.strip().replace("", "(blank)")
            )
            .groupby("_key")["_rev"]
            .sum()
            .sort_values(ascending=False)
        )
        if grouped.empty:
            return None
        top = grouped.head(8)
        frame = pd.DataFrame(
            {
                "name": [_short(n) for n in top.index],
                "revenue": top.to_numpy(dtype=float),
            }
        )
        frame["share"] = (
            frame["revenue"] / total * 100
            if total not in (0, 0.0)
            else frame["revenue"] * 0
        )
        frame["label"] = frame.apply(
            lambda r: f"{money(r['revenue'])} · {r['share']:.1f}%", axis=1
        )
        fig = px.bar(
            frame, x="revenue", y="name", orientation="h", text="label"
        )
        fig.update_traces(
            marker_color=ACCENT,
            marker_line_width=0,
            textposition="outside",
            cliponaxis=False,
            textfont={"size": 11, "color": "#475569"},
            hovertemplate="%{y}<br>$%{x:,.2f}<extra></extra>",
        )
        fig.update_layout(
            height=340,
            autosize=True,
            margin={"l": 10, "r": 90, "t": 10, "b": 35},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            showlegend=False,
            bargap=0.35,
        )
        fig.update_xaxes(
            title_text="", gridcolor=GRID, tickprefix="$", zerolinecolor=GRID
        )
        fig.update_yaxes(title_text="", autorange="reversed", showgrid=False)
        if kind == "customer":
            self.customer_figure = fig
        else:
            self.product_figure = fig
        leader = str(top.index[0])
        leader_share = _safe_div(_safe_float(top.iloc[0]), total) * 100
        return (_short(leader, 40), leader_share)

    def _build_retention(
        self, df: pd.DataFrame, cust_col: str, order_col: str = ""
    ) -> None:
        reference = df["_date"].max()
        span_days = max(0, int((reference - df["_date"].min()).days))
        self.months_observed = round(max(span_days / 30.44, 1.0), 2)
        self.reference_date = reference.strftime("%b %d, %Y")
        if not self.has_customer_data:
            self.repeat_customers = 0
            self.repeat_rate = 0.0
            self.repeat_basis = ""
            self.revenue_per_customer = 0.0
            self.avg_orders_per_customer = 0.0
            self.avg_lifespan_months = 0.0
            self.clv_estimate = 0.0
            self.clv_available = False
            self.clv_caption = "Needs a customer column"
            self.customer_activity = []
            self.active_customers = 0
            self.at_risk_customers = 0
            self.inactive_customers = 0
            self.inactive_revenue_display = "$0.00"
            self.retention_rate = 0.0
            self.inactivity_buckets = []
            self._clear_concentration()
            self.customer_figure = _blank_figure("No customer column mapped")
            return

        work = df.assign(
            _key=df[cust_col].astype(str).str.strip().replace("", "(blank)")
        )
        grouped = work.groupby("_key").agg(
            first_order=("_date", "min"),
            last_order=("_date", "max"),
            orders=("_rev", "size"),
            revenue=("_rev", "sum"),
        )
        if grouped.empty:
            self.has_customer_data = False
            self.repeat_customers = 0
            self.repeat_rate = 0.0
            self.repeat_basis = ""
            self.revenue_per_customer = 0.0
            self.avg_orders_per_customer = 0.0
            self.avg_lifespan_months = 0.0
            self.clv_estimate = 0.0
            self.clv_available = False
            self.clv_caption = "No customer values were present in those rows"
            self.customer_activity = []
            self.active_customers = 0
            self.at_risk_customers = 0
            self.inactive_customers = 0
            self.inactive_revenue_display = "$0.00"
            self.retention_rate = 0.0
            self.inactivity_buckets = []
            self._clear_concentration()
            self.customer_figure = _blank_figure("No customer values found")
            return
        if order_col and order_col in work.columns:
            keys = work[order_col].astype(str).str.strip()
            with_orders = work.assign(_order=keys)
            with_orders = with_orders[with_orders["_order"] != ""]
            distinct = with_orders.groupby("_key")["_order"].nunique()
            grouped["orders"] = (
                distinct.reindex(grouped.index).fillna(grouped["orders"])
            ).astype(int)
            self.repeat_basis = f"Distinct “{order_col}” values per customer"
        else:
            self.repeat_basis = "Cleaned rows per customer"
        grouped["days_since"] = (reference - grouped["last_order"]).dt.days
        grouped = grouped.sort_values("days_since", ascending=False)

        rows: list[CustomerRow] = []
        for name, row in grouped.iterrows():
            days = int(_safe_float(row["days_since"]))
            status = (
                "Inactive"
                if days >= INACTIVE_DAYS
                else ("At risk" if days >= AT_RISK_DAYS else "Active")
            )
            rows.append(
                CustomerRow(
                    name=_short(name, 32),
                    last_order=pd.Timestamp(row["last_order"]).strftime(
                        "%Y-%m-%d"
                    ),
                    days_since=days,
                    orders=int(_safe_float(row["orders"])),
                    revenue_display=money(_safe_float(row["revenue"])),
                    status=status,
                )
            )

        inactive = grouped[grouped["days_since"] >= INACTIVE_DAYS]
        at_risk = grouped[
            (grouped["days_since"] >= AT_RISK_DAYS)
            & (grouped["days_since"] < INACTIVE_DAYS)
        ]
        total_customers = int(len(grouped))
        self.inactive_customers = int(len(inactive))
        self.at_risk_customers = int(len(at_risk))
        self.active_customers = total_customers - self.inactive_customers
        self.inactive_revenue_display = money(
            _safe_float(inactive["revenue"].sum())
        )
        self.retention_rate = round(
            _safe_div(self.active_customers, total_customers) * 100, 1
        )
        self.customer_activity = rows[:25]
        self._build_buckets(inactive)
        self._build_concentration(grouped)

        repeat = grouped[grouped["orders"] > 1]
        self.repeat_customers = int(len(repeat))
        self.repeat_rate = round(
            _safe_div(self.repeat_customers, total_customers) * 100, 1
        )
        self.revenue_per_customer = round(
            _safe_div(_safe_float(grouped["revenue"].sum()), total_customers), 2
        )
        self.avg_orders_per_customer = round(
            _safe_float(grouped["orders"].mean()), 2
        )
        lifespans = (
            grouped["last_order"] - grouped["first_order"]
        ).dt.days / 30.44
        self.avg_lifespan_months = round(_safe_float(lifespans.mean()), 2)
        if self.repeat_customers > 0 and self.avg_lifespan_months > 0:
            frequency = _safe_div(
                self.avg_orders_per_customer, self.months_observed
            )
            self.clv_estimate = round(
                self.aov * frequency * self.avg_lifespan_months, 2
            )
            self.clv_available = True
            self.clv_caption = (
                f"{self.aov_display} AOV × {frequency:.2f} orders/month × "
                f"{self.avg_lifespan_months:.1f} month lifespan"
            )
        else:
            self.clv_estimate = 0.0
            self.clv_available = False
            self.clv_caption = (
                "No customer in this range ordered on more than one date, "
                "so no lifespan can be measured"
            )

    def _build_summary(
        self,
        top_customer: tuple[str, float] | None,
        top_product: tuple[str, float] | None,
    ) -> None:
        points: list[str] = [
            f"{self.order_count:,} cleaned rows totalling {self.total_revenue_display} "
            f"between {self.period_start} and {self.period_end}.",
            f"Average order value is {self.aov_display} across {self.order_count:,} rows.",
        ]
        if self.has_customer_data:
            points.append(
                f"{self.customer_count:,} distinct customers appear in the mapped customer column."
            )
        if self.has_growth and self.previous_month:
            verb = (
                "grew"
                if self.growth_direction == "up"
                else (
                    "fell" if self.growth_direction == "down" else "held flat"
                )
            )
            points.append(
                f"{self.comparison_label} {verb} {abs(self.revenue_growth):.1f}% — "
                f"{self.growth_caption}."
            )
            if self.partial_month_note:
                points.append(self.partial_month_note)
        elif self.latest_month:
            points.append(
                f"All rows fall in {self.latest_month}, so month-over-month growth isn't available yet."
            )
        if self.best_period_label:
            points.append(
                f"Strongest {self.granularity.lower()} period is {self.best_period_label} "
                f"at {self.best_period_display}."
            )
        if top_customer:
            points.append(
                f"{top_customer[0]} is the largest customer at {top_customer[1]:.1f}% of revenue."
            )
        if top_product:
            points.append(
                f"{top_product[0]} leads products with {top_product[1]:.1f}% of revenue."
            )
        if self.has_customer_data:
            points.append(
                f"{self.repeat_customers:,} of {self.customer_count:,} customers ordered more than once "
                f"({self.repeat_rate:.1f}% repeat rate, based on {self.repeat_basis.lower()})."
            )
            points.append(
                f"{self.inactive_customers:,} potentially inactive customer(s) have not ordered "
                f"in {INACTIVE_DAYS}+ days as of {self.reference_date}. Historical revenue from "
                f"potentially inactive customers totals {self.inactive_revenue_display}. "
                f"{INACTIVE_NOTE}"
            )
            for bucket in self.inactivity_buckets:
                if bucket["customers"]:
                    points.append(
                        f"Inactive {bucket['label']}: {bucket['customers']:,} customer(s) with "
                        f"{bucket['revenue_display']} of historical revenue "
                        f"({bucket['share_display']} of the inactive total)."
                    )
        if self.has_concentration:
            points.append(
                f"Customer concentration is {self.concentration_level.lower()} — top 1 customer "
                f"{self.top1_share:.1f}%, top {self.top5_count} {self.top5_share:.1f}%, "
                f"top {self.top10_count} {self.top10_share:.1f}% of revenue."
            )
        if self.large_change_detected:
            points.append(
                f"{self.comparison_label} moved more than {LARGE_CHANGE_THRESHOLD:.0f}%. "
                f"{LARGE_CHANGE_MESSAGE}"
            )
        if self.filters_applied:
            points.append(
                f"{self.filtered_rows:,} of {self.source_rows:,} rows match the "
                f"{self.filters_applied} filter(s) currently applied."
            )
        self.summary_points = points
        self._build_highlights(top_customer, top_product)

    def _highlight(
        self,
        key: str,
        label: str,
        value: str,
        detail: str,
        icon: str,
        tone: str = "flat",
        available: bool = True,
    ) -> Highlight:
        return Highlight(
            key=key,
            label=label,
            value=value if available else NOT_AVAILABLE,
            detail=detail,
            icon=icon,
            tone=tone if available else "flat",
            available=available,
        )

    def _build_highlights(
        self,
        top_customer: tuple[str, float] | None,
        top_product: tuple[str, float] | None,
    ) -> None:
        """Five headline facts: revenue, growth, top contributor, customers, risk."""
        cards: list[Highlight] = [
            self._highlight(
                "revenue",
                "Current revenue",
                self.total_revenue_display,
                f"{self.period_start} → {self.period_end} · {self.order_count:,} orders",
                "dollar-sign",
            )
        ]

        if self.has_growth:
            verb = (
                "growth"
                if self.growth_direction == "up"
                else ("decline" if self.growth_direction == "down" else "flat")
            )
            cards.append(
                self._highlight(
                    "growth",
                    f"Revenue {verb}",
                    self.growth_display,
                    f"{self.growth_caption} · {self.latest_revenue_display} latest month",
                    "trending-up"
                    if self.growth_direction == "up"
                    else "trending-down",
                    tone=self.growth_direction,
                )
            )
        else:
            cards.append(
                self._highlight(
                    "growth",
                    "Revenue growth",
                    "",
                    "At least two months of history are needed to compare.",
                    "trending-up",
                    available=False,
                )
            )

        if top_customer:
            cards.append(
                self._highlight(
                    "contributor",
                    "Top revenue contributor",
                    top_customer[0],
                    f"{top_customer[1]:.1f}% of revenue (largest customer)",
                    "crown",
                    tone="flat",
                )
            )
        elif top_product:
            cards.append(
                self._highlight(
                    "contributor",
                    "Top revenue contributor",
                    top_product[0],
                    f"{top_product[1]:.1f}% of revenue (largest product)",
                    "package",
                )
            )
        elif self.best_period_label:
            cards.append(
                self._highlight(
                    "contributor",
                    "Strongest period",
                    self.best_period_display,
                    f"{self.best_period_label} led all {self.granularity.lower()} periods",
                    "award",
                )
            )
        else:
            cards.append(
                self._highlight(
                    "contributor",
                    "Top revenue contributor",
                    "",
                    "Map a customer or product column to rank contributors.",
                    "crown",
                    available=False,
                )
            )

        if self.has_customer_data:
            trend_tone = (
                "up"
                if self.retention_rate >= 80
                else ("down" if self.retention_rate < 50 else "flat")
            )
            cards.append(
                self._highlight(
                    "customers",
                    "Customer trend",
                    f"{self.customer_count:,} customers",
                    f"{self.retention_rate:.1f}% retained · {self.repeat_rate:.1f}% repeat · "
                    f"{self.inactive_customers:,} inactive {INACTIVE_DAYS}+ days",
                    "users",
                    tone=trend_tone,
                )
            )
        else:
            cards.append(
                self._highlight(
                    "customers",
                    "Customer trend",
                    "",
                    "Map a customer column to measure retention and repeat buying.",
                    "users",
                    available=False,
                )
            )

        cards.append(self._risk_highlight(top_customer, top_product))
        self.executive_highlights = cards

    def _risk_highlight(
        self,
        top_customer: tuple[str, float] | None,
        top_product: tuple[str, float] | None,
    ) -> Highlight:
        if self.growth_direction == "down" and self.has_growth:
            return self._highlight(
                "risk",
                "Biggest risk",
                f"Revenue down {abs(self.revenue_growth):.1f}%",
                f"{self.growth_caption} — investigate the products and accounts that moved.",
                "triangle-alert",
                tone="down",
            )
        if self.has_customer_data and self.inactive_customers > 0:
            return self._highlight(
                "risk",
                "Potentially inactive customers",
                f"{self.inactive_customers:,} customers",
                f"{self.inactive_revenue_display} of historical revenue is associated with "
                f"customers silent for {INACTIVE_DAYS}+ days as of {self.reference_date}. "
                "This is not a prediction of future revenue loss.",
                "user-x",
                tone="down",
            )
        if top_customer and top_customer[1] >= 30:
            return self._highlight(
                "risk",
                "Biggest risk",
                f"{top_customer[1]:.1f}% concentration",
                f"{top_customer[0]} alone carries that share of revenue.",
                "chart-pie",
                tone="down",
            )
        if top_product and top_product[1] >= 40:
            return self._highlight(
                "risk",
                "Biggest risk",
                f"{top_product[1]:.1f}% concentration",
                f"{top_product[0]} carries that share of revenue on its own.",
                "chart-pie",
                tone="down",
            )
        if self.has_growth and self.growth_direction == "up":
            return self._highlight(
                "risk",
                "Biggest opportunity",
                f"Momentum {self.growth_display}",
                f"{self.growth_caption} — repeat whatever drove the latest month.",
                "rocket",
                tone="up",
            )
        if self.best_period_label:
            return self._highlight(
                "risk",
                "Biggest opportunity",
                self.best_period_display,
                f"{self.best_period_label} is your proven peak — plan around that pattern.",
                "rocket",
                tone="up",
            )
        return self._highlight(
            "risk",
            "Risk & opportunity",
            "",
            "Not enough history or columns to single out a risk or opportunity yet.",
            "triangle-alert",
            available=False,
        )

    def _kpi(
        self,
        key: str,
        label: str,
        icon: str,
        value: str,
        caption: str,
        available: bool = True,
        tone: str = "flat",
    ) -> KPI:
        return KPI(
            key=key,
            label=label,
            icon=icon,
            value=value if available else NOT_AVAILABLE,
            caption=caption,
            available=available,
            tone=tone if available else "flat",
        )

    def _build_kpis(self) -> None:
        has_cust = self.has_customer_data
        no_cust = "No customer column is mapped, so this can't be calculated"
        cards: list[KPI] = [
            self._kpi(
                "revenue",
                "Total revenue",
                "dollar-sign",
                self.total_revenue_display,
                f"{self.period_start} → {self.period_end}",
            ),
            self._kpi(
                "orders",
                "Total orders",
                "receipt",
                f"{self.order_count:,}",
                self.order_caption,
            ),
            self._kpi(
                "customers",
                "Total customers",
                "users",
                f"{self.customer_count:,}",
                "Distinct values in the customer column",
                available=has_cust,
                tone="flat",
            ),
            self._kpi(
                "aov",
                "Average order value",
                "calculator",
                self.aov_display,
                "Total revenue ÷ orders",
                available=self.order_count > 0,
            ),
            self._kpi(
                "growth",
                self.growth_metric_label,
                "trending-up",
                self.growth_display,
                self.growth_caption,
                available=self.has_growth,
                tone=self.growth_direction,
            ),
            self._kpi(
                "repeat",
                "Repeat customer rate",
                "repeat",
                f"{self.repeat_rate:.1f}%",
                (
                    f"{self.repeat_customers:,} of {self.customer_count:,} ordered more than once"
                    if has_cust
                    else no_cust
                ),
                available=has_cust,
            ),
            self._kpi(
                "retention",
                "Customer retention rate",
                "heart-pulse",
                f"{self.retention_rate:.1f}%",
                (
                    f"Ordered within {INACTIVE_DAYS} days of {self.reference_date}"
                    if has_cust
                    else no_cust
                ),
                available=has_cust,
            ),
            self._kpi(
                "churn",
                "Potentially inactive customers",
                "user-x",
                f"{self.inactive_customers:,}",
                (
                    f"No order in {INACTIVE_DAYS}+ days · {self.inactive_revenue_display} "
                    "of historical revenue (not a predicted loss)"
                    if has_cust
                    else no_cust
                ),
                available=has_cust,
            ),
            self._kpi(
                "concentration",
                "Customer concentration",
                "chart-pie",
                self.concentration_level,
                (
                    f"Top 1 {self.top1_share:.1f}% · top {self.top5_count} {self.top5_share:.1f}% "
                    f"· top {self.top10_count} {self.top10_share:.1f}% of revenue"
                    if self.has_concentration
                    else no_cust
                ),
                available=self.has_concentration,
                tone="flat",
            ),
            self._kpi(
                "rev_per_customer",
                "Revenue per customer",
                "user-round",
                money(self.revenue_per_customer),
                (
                    f"Across {self.customer_count:,} customers in this range"
                    if has_cust
                    else no_cust
                ),
                available=has_cust,
            ),
            self._kpi(
                "clv",
                "Customer lifetime value",
                "gem",
                money(self.clv_estimate),
                (self.clv_caption if has_cust else no_cust),
                available=has_cust and self.clv_available,
            ),
        ]
        self.kpi_cards = cards
