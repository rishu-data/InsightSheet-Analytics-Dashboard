import logging
import math
from typing import TypedDict

import pandas as pd
import plotly.graph_objects as go
import reflex as rx

from app.states.dashboard_state import (
    _blank_figure,
    _col,
    _safe_div,
    _safe_float,
    _short,
    _to_datetime,
    _to_number,
    money,
)

INDIGO = "#4f46e5"
FADED = "#c7d2fe"
GRID = "#eef2f7"

ALL_SEGMENTS = "All segments"

INSUFFICIENT_DATA = (
    "RFM analysis is unavailable because the uploaded dataset does not contain "
    "sufficient customer transaction information."
)

# Below this many distinct customers, percentile buckets are unreliable.
MIN_CUSTOMERS_FOR_QUANTILES = 5

SORT_KEYS: tuple[str, ...] = (
    "name",
    "segment",
    "recency",
    "frequency",
    "monetary",
    "score",
)

# Segment name -> (icon, tone, plain-English meaning, scoring rule)
SEGMENT_META: dict[str, tuple[str, str, str, str]] = {
    "Champions": (
        "crown",
        "good",
        "Bought recently, buy often and spend the most in your file.",
        "Recency score 4–5 and the average of Frequency & Monetary is 4 or more",
    ),
    "Loyal Customers": (
        "heart",
        "good",
        "Consistent buyers with solid spend across the period analysed.",
        "Recency score 3 or more and the average of Frequency & Monetary is 3 or more",
    ),
    "Potential Loyalists": (
        "sprout",
        "info",
        "Recent buyers with moderate frequency or spend that could grow.",
        "Recency score 4–5 and the average of Frequency & Monetary is 2 or more",
    ),
    "New Customers": (
        "user-plus",
        "info",
        "Bought very recently, but not often and not much yet.",
        "Recency score 4–5 with a Frequency & Monetary average below 2",
    ),
    "At Risk": (
        "triangle-alert",
        "warn",
        "Used to buy regularly, but purchases have slowed down.",
        "Recency score 3 or below with a Frequency & Monetary average of 2 or more",
    ),
    "Cannot Lose Them": (
        "life-buoy",
        "risk",
        "High past frequency and spend, but no recent purchase at all.",
        "Recency score 2 or below with a Frequency & Monetary average of 4 or more",
    ),
    "Potentially Inactive": (
        "moon",
        "risk",
        "No recent purchases and low frequency or spend — quiet, not confirmed lost.",
        "Recency score 2 or below with a Frequency & Monetary average below 2",
    ),
}

SEGMENT_ORDER: list[str] = list(SEGMENT_META.keys())

# Segment name -> (title, recommended action, priority, icon)
RECOMMENDED_ACTIONS: dict[str, tuple[str, str, str, str]] = {
    "Champions": (
        "Reward and retain your Champions",
        "Consider early access, loyalty perks or a named account owner so this buying "
        "pattern keeps going. This is a recommendation, not a guaranteed outcome.",
        "High",
        "crown",
    ),
    "Loyal Customers": (
        "Grow Loyal Customers toward Champion behaviour",
        "Bundles, upsells or referral incentives are the usual levers on frequency and "
        "spend for this group. Review each idea against what you know about them.",
        "Medium",
        "heart",
    ),
    "Potential Loyalists": (
        "Deepen the relationship with Potential Loyalists",
        "A membership, subscription or repeat-purchase incentive while they are still "
        "engaged is a reasonable next step to test.",
        "Medium",
        "sprout",
    ),
    "New Customers": (
        "Onboard New Customers deliberately",
        "A follow-up shortly after the first purchase, plus a second-order offer, is the "
        "cheapest way to test whether they repeat.",
        "Medium",
        "user-plus",
    ),
    "At Risk": (
        "Re-engage At Risk customers before the gap widens",
        "A personal outreach with a tailored offer is suggested — these customers bought "
        "before, so the revenue is already proven.",
        "High",
        "triangle-alert",
    ),
    "Cannot Lose Them": (
        "Prioritise the Cannot Lose Them accounts",
        "These accounts spent heavily before going quiet. A direct win-back conversation "
        "is suggested first, ahead of broad campaigns.",
        "High",
        "life-buoy",
    ),
    "Potentially Inactive": (
        "Test a low-cost win-back on Potentially Inactive customers",
        "Treat this group as quiet rather than confirmed lost, and measure the response "
        "before spending more on them.",
        "Low",
        "moon",
    ),
}


class RFMCustomer(TypedDict):
    name: str
    last_order: str
    recency: int
    frequency: int
    monetary: float
    monetary_display: str
    avg_order_display: str
    r: int
    f: int
    m: int
    rfm: str
    score_total: int
    segment: str
    tone: str


class RFMSegment(TypedDict):
    name: str
    icon: str
    tone: str
    description: str
    rule: str
    customers: int
    share_display: str
    revenue: float
    revenue_share: float
    revenue_display: str
    revenue_share_display: str
    avg_recency: int
    avg_frequency_display: str
    avg_monetary_display: str


class RFMInsight(TypedDict):
    key: str
    label: str
    value: str
    detail: str
    icon: str
    tone: str


class RFMRecommendation(TypedDict):
    key: str
    segment: str
    title: str
    detail: str
    priority: str
    icon: str
    scope: str


def _quantile_score(values: pd.Series, reverse: bool) -> pd.Series:
    """Turn a metric into a 1–5 score using percentile (quantile) ranks."""
    if len(values) <= 1:
        return pd.Series([3] * len(values), index=values.index, dtype=int)
    pct = values.rank(method="average", pct=True).fillna(0.5)
    scores = pct.map(
        lambda v: min(5, max(1, math.ceil(_safe_float(v, 0.5) * 5)))
    )
    if reverse:
        scores = 6 - scores
    return scores.astype(int)


def _simple_score(values: pd.Series, reverse: bool) -> pd.Series:
    """Deterministic min–max fallback when there are too few customers.

    With only a handful of customers, percentile buckets are meaningless, so each
    value is placed on an equal-width 1–5 scale between the smallest and largest
    value actually present in the data.
    """
    numbers = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    if len(numbers) == 0:
        return pd.Series([], index=numbers.index, dtype=int)
    low = _safe_float(numbers.min())
    high = _safe_float(numbers.max())
    if high <= low:
        return pd.Series([3] * len(numbers), index=numbers.index, dtype=int)
    span = high - low
    scores = numbers.map(
        lambda v: min(
            5,
            max(
                1,
                int(math.floor(_safe_div(_safe_float(v) - low, span) * 5)) + 1,
            ),
        )
    )
    if reverse:
        scores = 6 - scores
    return scores.astype(int)


def _segment_for(r: int, f: int, m: int) -> str:
    """Deterministic segment from the 1–5 R/F/M scores.

    No customer is ever labelled permanently churned — the quietest group is only
    ever described as potentially inactive.
    """
    fm = (f + m) / 2
    if r >= 4 and fm >= 4:
        return "Champions"
    if r >= 3 and fm >= 3:
        return "Loyal Customers"
    if r >= 4 and fm >= 2:
        return "Potential Loyalists"
    if r >= 4:
        return "New Customers"
    if r <= 2 and fm >= 4:
        return "Cannot Lose Them"
    if fm >= 2:
        return "At Risk"
    return "Potentially Inactive"


class RFMState(rx.State):
    available: bool = False
    blocked_reason: str = INSUFFICIENT_DATA
    missing_hints: list[str] = []

    reference_date: str = ""
    frequency_basis: str = "Cleaned rows per customer"
    customer_total: int = 0
    rows_used: int = 0
    rows_skipped: int = 0
    total_revenue_display: str = "$0.00"

    avg_recency: int = 0
    avg_frequency_display: str = "0.0"
    avg_monetary_display: str = "$0.00"
    median_recency: int = 0

    scoring_simplified: bool = False
    scoring_note: str = ""

    segments: list[RFMSegment] = []
    customers: list[RFMCustomer] = []
    insights: list[RFMInsight] = []
    recommendations: list[RFMRecommendation] = []
    segment_figure: go.Figure = _blank_figure("No customer segments yet")
    segment_revenue_figure: go.Figure = _blank_figure(
        "No revenue contribution yet"
    )
    segment_options: list[str] = [ALL_SEGMENTS]
    selected_segment: str = ALL_SEGMENTS

    # Table controls (never mutate `customers` — filtering happens on a copy)
    search_query: str = ""
    sort_key: str = "monetary"
    sort_desc: bool = True
    table_key: int = 0

    top_segment: str = ""
    top_segment_customers: int = 0
    top_revenue_segment: str = ""
    top_revenue_segment_display: str = "$0.00"
    top_revenue_segment_share: str = "0.0%"
    champion_customers: int = 0
    champion_revenue_display: str = "$0.00"
    champion_revenue_share: str = "0.0%"
    at_risk_customers: int = 0
    at_risk_revenue_display: str = "$0.00"
    cannot_lose_customers: int = 0
    cannot_lose_revenue_display: str = "$0.00"
    inactive_customers: int = 0
    inactive_revenue_display: str = "$0.00"
    new_customers: int = 0
    loyal_customers: int = 0
    loyal_revenue_display: str = "$0.00"
    potential_loyalists: int = 0

    summary_points: list[str] = []

    @rx.var
    def filtered_customers(self) -> list[RFMCustomer]:
        """Segment filter + search + sort applied to a copy of the scored rows."""
        rows: list[RFMCustomer] = list(self.customers)
        if self.selected_segment != ALL_SEGMENTS:
            rows = [
                row for row in rows if row["segment"] == self.selected_segment
            ]
        query = self.search_query.strip().lower()
        if query:
            rows = [
                row
                for row in rows
                if query in row["name"].lower()
                or query in row["segment"].lower()
            ]
        key = self.sort_key if self.sort_key in SORT_KEYS else "monetary"
        if key == "name":
            rows = sorted(
                rows, key=lambda r: r["name"].lower(), reverse=self.sort_desc
            )
        elif key == "segment":
            rows = sorted(
                rows,
                key=lambda r: (r["segment"].lower(), -r["monetary"]),
                reverse=self.sort_desc,
            )
        elif key == "recency":
            rows = sorted(
                rows, key=lambda r: r["recency"], reverse=self.sort_desc
            )
        elif key == "frequency":
            rows = sorted(
                rows, key=lambda r: r["frequency"], reverse=self.sort_desc
            )
        elif key == "score":
            rows = sorted(
                rows, key=lambda r: r["score_total"], reverse=self.sort_desc
            )
        else:
            rows = sorted(
                rows, key=lambda r: r["monetary"], reverse=self.sort_desc
            )
        return rows

    @rx.var
    def visible_customers(self) -> list[RFMCustomer]:
        return self.filtered_customers[:100]

    @rx.var
    def match_count(self) -> int:
        return len(self.filtered_customers)

    @rx.var
    def has_visible_customers(self) -> bool:
        return len(self.visible_customers) > 0

    @rx.var
    def table_controls_active(self) -> bool:
        return bool(
            self.search_query.strip() or self.selected_segment != ALL_SEGMENTS
        )

    @rx.var
    def sort_direction_label(self) -> str:
        return "Highest first" if self.sort_desc else "Lowest first"

    @rx.var
    def visible_count_label(self) -> str:
        shown = len(self.visible_customers)
        matches = self.match_count
        if matches == self.customer_total:
            return f"Showing {shown} of {self.customer_total} scored customers"
        return (
            f"Showing {shown} of {matches} matching customer(s) "
            f"out of {self.customer_total} scored"
        )

    @rx.var
    def has_insights(self) -> bool:
        return len(self.insights) > 0

    @rx.var
    def has_recommendations(self) -> bool:
        return len(self.recommendations) > 0

    @rx.event
    def select_segment(self, value: str):
        self.selected_segment = (
            value if value in self.segment_options else ALL_SEGMENTS
        )
        self._build_figure()
        self._build_revenue_figure()

    @rx.event
    def set_search(self, value: str):
        self.search_query = str(value or "")

    @rx.event
    def set_sort_key(self, value: str):
        key = str(value or "monetary")
        self.sort_key = key if key in SORT_KEYS else "monetary"
        self.sort_desc = self.sort_key not in ("name", "segment")

    @rx.event
    def toggle_sort_direction(self):
        self.sort_desc = not self.sort_desc

    @rx.event
    def sort_by(self, key: str):
        column = str(key or "monetary")
        if column not in SORT_KEYS:
            column = "monetary"
        if column == self.sort_key:
            self.sort_desc = not self.sort_desc
            return
        self.sort_key = column
        self.sort_desc = column not in ("name", "segment")

    @rx.event
    def clear_table_controls(self):
        self.search_query = ""
        self.selected_segment = ALL_SEGMENTS
        self.sort_key = "monetary"
        self.sort_desc = True
        self.table_key += 1
        self._build_figure()
        self._build_revenue_figure()

    @rx.event
    async def compute_rfm(self):
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        if not records:
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll segment your customers from the cleaned rows.",
                [
                    "A customer column (name, email or ID)",
                    "A date column",
                    "A revenue column",
                ],
            )
            return
        missing: list[str] = []
        if not _col(mapping, "customer"):
            missing.append("A customer column (name, email or ID)")
        if not _col(mapping, "date"):
            missing.append("A date column")
        if not _col(mapping, "revenue"):
            missing.append("A revenue column")
        if missing:
            self._unavailable(
                "RFM segmentation needs customer, date and revenue columns. Map them on the upload page to unlock this tab.",
                missing,
            )
            return
        try:
            self._build(records, mapping)
        except Exception as e:
            logging.exception(f"Error computing RFM segments: {e}")
            self._unavailable(
                "We couldn't build RFM segments from those columns. Try mapping a different customer, date or revenue column.",
                ["Readable dates and numeric revenue on the same row"],
            )

    def _unavailable(self, reason: str, hints: list[str]) -> None:
        """Block the section. The user-facing reason is always the same message."""
        self.available = False
        self.blocked_reason = INSUFFICIENT_DATA
        self.missing_hints = hints
        self.reference_date = ""
        self.frequency_basis = "Cleaned rows per customer"
        self.customer_total = 0
        self.rows_used = 0
        self.rows_skipped = 0
        self.total_revenue_display = "$0.00"
        self.avg_recency = 0
        self.avg_frequency_display = "0.0"
        self.avg_monetary_display = "$0.00"
        self.median_recency = 0
        self.scoring_simplified = False
        self.scoring_note = ""
        self.segments = []
        self.customers = []
        self.insights = []
        self.recommendations = []
        self.segment_figure = _blank_figure("No customer segments yet")
        self.segment_revenue_figure = _blank_figure(
            "No revenue contribution yet"
        )
        self.segment_options = [ALL_SEGMENTS]
        self.selected_segment = ALL_SEGMENTS
        self.search_query = ""
        self.sort_key = "monetary"
        self.sort_desc = True
        self.table_key += 1
        self.top_segment = ""
        self.top_segment_customers = 0
        self.top_revenue_segment = ""
        self.top_revenue_segment_display = "$0.00"
        self.top_revenue_segment_share = "0.0%"
        self.champion_customers = 0
        self.champion_revenue_display = "$0.00"
        self.champion_revenue_share = "0.0%"
        self.at_risk_customers = 0
        self.at_risk_revenue_display = "$0.00"
        self.cannot_lose_customers = 0
        self.cannot_lose_revenue_display = "$0.00"
        self.inactive_customers = 0
        self.inactive_revenue_display = "$0.00"
        self.new_customers = 0
        self.loyal_customers = 0
        self.loyal_revenue_display = "$0.00"
        self.potential_loyalists = 0
        self.summary_points = []

    def _build(
        self, records: list[dict[str, str]], mapping: dict[str, str]
    ) -> None:
        if not records:
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll segment your customers from the cleaned rows.",
                [
                    "A customer column (name, email or ID)",
                    "A date column",
                    "A revenue column",
                ],
            )
            return
        cust_col = _col(mapping, "customer")
        date_col = _col(mapping, "date")
        rev_col = _col(mapping, "revenue")
        order_col = _col(mapping, "order_id")
        missing_roles: list[str] = []
        if not cust_col:
            missing_roles.append("A customer column (name, email or ID)")
        if not date_col:
            missing_roles.append("A date column")
        if not rev_col:
            missing_roles.append("A revenue column")
        if missing_roles:
            self._unavailable(
                "RFM segmentation needs customer, date and revenue columns. Map them on the upload page to unlock this tab.",
                missing_roles,
            )
            return

        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._unavailable(
                "There are no cleaned rows to score customers from yet.",
                ["At least one row with a customer, a date and an amount"],
            )
            return
        for col in (cust_col, date_col, rev_col):
            if col not in df.columns:
                self._unavailable(
                    "The mapped columns are no longer in the cleaned file. Re-check your mapping on the upload page.",
                    [
                        "Customer, date and revenue columns that exist in the file"
                    ],
                )
                return

        total_rows = int(len(df))
        df["_date"] = _to_datetime(df[date_col])
        df["_rev"] = _to_number(df[rev_col])
        df["_key"] = df[cust_col].astype(str).str.strip()
        df = df[~df["_key"].str.lower().isin(("nan", "none", "null"))]
        df = df.dropna(subset=["_date", "_rev"])
        df = df[df["_key"].str.len() > 0]
        if df.empty:
            self._unavailable(
                "No rows had a customer, a readable date and a numeric revenue value at the same time.",
                ["Customer, date and revenue values on the same row"],
            )
            return

        self.rows_used = int(len(df))
        self.rows_skipped = max(0, total_rows - self.rows_used)

        reference = df["_date"].max()
        self.reference_date = reference.strftime("%b %d, %Y")

        use_orders = bool(order_col) and order_col in df.columns
        grouped = df.groupby("_key").agg(
            last_order=("_date", "max"),
            rows=("_rev", "size"),
            monetary=("_rev", "sum"),
        )
        if use_orders:
            keys = df[order_col].astype(str).str.strip()
            work = df.assign(_order=keys)
            work = work[work["_order"] != ""]
            distinct = work.groupby("_key")["_order"].nunique()
            grouped["frequency"] = (
                distinct.reindex(grouped.index).fillna(grouped["rows"])
            ).astype(int)
            self.frequency_basis = f"Distinct “{order_col}” values per customer"
        else:
            grouped["frequency"] = grouped["rows"].astype(int)
            self.frequency_basis = "Cleaned rows per customer"

        if grouped.empty:
            self._unavailable(
                "No customer values were left after cleaning, so nothing can be scored.",
                ["Customer names, emails or IDs on the same row as a sale"],
            )
            return
        grouped["recency"] = (
            (reference - grouped["last_order"]).dt.days.fillna(0).astype(int)
        )
        customer_count = int(len(grouped))
        self.scoring_simplified = customer_count < MIN_CUSTOMERS_FOR_QUANTILES
        scorer = _simple_score if self.scoring_simplified else _quantile_score
        grouped["r"] = scorer(grouped["recency"], True)
        grouped["f"] = scorer(grouped["frequency"], False)
        grouped["m"] = scorer(grouped["monetary"], False)
        if self.scoring_simplified:
            self.scoring_note = (
                f"Scoring was simplified: only {customer_count} distinct customer(s) were "
                f"found, which is too few for reliable percentile buckets. Each score is "
                "placed on an equal-width 1–5 scale between the smallest and largest value "
                "in your own data instead."
            )
        else:
            self.scoring_note = (
                f"Each of the {customer_count} customers was ranked against the others and "
                "placed in a 1–5 percentile band per metric. Recency is reversed so a more "
                "recent purchase scores higher; frequency and monetary value score higher "
                "when they are larger."
            )
        grouped["segment"] = [
            _segment_for(int(r), int(f), int(m))
            for r, f, m in zip(grouped["r"], grouped["f"], grouped["m"])
        ]
        grouped = grouped.sort_values(
            ["m", "f", "recency"], ascending=[False, False, True]
        )

        total_revenue = _safe_float(grouped["monetary"].sum())
        self.total_revenue_display = money(total_revenue)
        self.customer_total = int(len(grouped))
        self.avg_recency = int(round(_safe_float(grouped["recency"].mean())))
        self.median_recency = int(
            round(_safe_float(grouped["recency"].median()))
        )
        self.avg_frequency_display = (
            f"{_safe_float(grouped['frequency'].mean()):.1f}"
        )
        self.avg_monetary_display = money(
            _safe_float(grouped["monetary"].mean())
        )

        rows: list[RFMCustomer] = []
        for name, row in grouped.iterrows():
            segment = str(row["segment"])
            meta = SEGMENT_META.get(segment)
            tone = meta[1] if meta else "info"
            frequency = int(_safe_float(row["frequency"]))
            monetary = _safe_float(row["monetary"])
            r_score = int(row["r"])
            f_score = int(row["f"])
            m_score = int(row["m"])
            rows.append(
                RFMCustomer(
                    name=_short(name, 32),
                    last_order=pd.Timestamp(row["last_order"]).strftime(
                        "%Y-%m-%d"
                    ),
                    recency=int(row["recency"]),
                    frequency=frequency,
                    monetary=round(monetary, 2),
                    monetary_display=money(monetary),
                    avg_order_display=money(_safe_div(monetary, frequency)),
                    r=r_score,
                    f=f_score,
                    m=m_score,
                    rfm=f"{r_score}-{f_score}-{m_score}",
                    score_total=r_score + f_score + m_score,
                    segment=segment,
                    tone=tone,
                )
            )
        self.customers = rows

        self.selected_segment = ALL_SEGMENTS
        self.search_query = ""
        self.sort_key = "monetary"
        self.sort_desc = True
        self.table_key += 1
        self._build_segments(grouped, total_revenue)
        self._build_figure()
        self._build_revenue_figure()
        self._build_summary()
        self._build_insights(total_revenue)
        self.available = True
        self.blocked_reason = ""
        self.missing_hints = []

    def _build_segments(
        self, grouped: pd.DataFrame, total_revenue: float
    ) -> None:
        summaries: list[RFMSegment] = []
        for name in SEGMENT_ORDER:
            block = grouped[grouped["segment"] == name]
            if block.empty:
                continue
            icon, tone, description, rule = SEGMENT_META.get(
                name, ("user-round", "info", "", "")
            )
            count = int(len(block))
            revenue = _safe_float(block["monetary"].sum())
            revenue_share = _safe_div(revenue, total_revenue) * 100
            summaries.append(
                RFMSegment(
                    name=name,
                    icon=icon,
                    tone=tone,
                    description=description,
                    rule=rule,
                    customers=count,
                    share_display=f"{_safe_div(count, len(grouped)) * 100:.1f}%",
                    revenue=round(revenue, 2),
                    revenue_share=round(revenue_share, 1),
                    revenue_display=money(revenue),
                    revenue_share_display=f"{revenue_share:.1f}%",
                    avg_recency=int(
                        round(_safe_float(block["recency"].mean()))
                    ),
                    avg_frequency_display=f"{_safe_float(block['frequency'].mean()):.1f}",
                    avg_monetary_display=money(
                        _safe_float(block["monetary"].mean())
                    ),
                )
            )
        self.segments = summaries
        self.segment_options = [ALL_SEGMENTS] + [s["name"] for s in summaries]

        if summaries:
            by_customers = max(summaries, key=lambda s: s["customers"])
            self.top_segment = by_customers["name"]
            self.top_segment_customers = by_customers["customers"]
            leader = max(summaries, key=lambda s: s["revenue"])
            self.top_revenue_segment = leader["name"]
            self.top_revenue_segment_display = leader["revenue_display"]
            self.top_revenue_segment_share = leader["revenue_share_display"]

        champions = grouped[grouped["segment"] == "Champions"]
        champion_revenue = _safe_float(champions["monetary"].sum())
        self.champion_customers = int(len(champions))
        self.champion_revenue_display = money(champion_revenue)
        self.champion_revenue_share = (
            f"{_safe_div(champion_revenue, total_revenue) * 100:.1f}%"
        )
        risky = grouped[grouped["segment"] == "At Risk"]
        self.at_risk_customers = int(len(risky))
        self.at_risk_revenue_display = money(
            _safe_float(risky["monetary"].sum())
        )
        cannot_lose = grouped[grouped["segment"] == "Cannot Lose Them"]
        self.cannot_lose_customers = int(len(cannot_lose))
        self.cannot_lose_revenue_display = money(
            _safe_float(cannot_lose["monetary"].sum())
        )
        inactive = grouped[grouped["segment"] == "Potentially Inactive"]
        self.inactive_customers = int(len(inactive))
        self.inactive_revenue_display = money(
            _safe_float(inactive["monetary"].sum())
        )
        loyal = grouped[grouped["segment"] == "Loyal Customers"]
        self.loyal_customers = int(len(loyal))
        self.loyal_revenue_display = money(_safe_float(loyal["monetary"].sum()))
        self.new_customers = int(
            len(grouped[grouped["segment"] == "New Customers"])
        )
        self.potential_loyalists = int(
            len(grouped[grouped["segment"] == "Potential Loyalists"])
        )

    def _build_figure(self) -> None:
        if not self.segments:
            self.segment_figure = _blank_figure("No customer segments yet")
            return
        names = [s["name"] for s in self.segments]
        counts = [s["customers"] for s in self.segments]
        labels = [
            f"{s['customers']} · {s['revenue_display']}" for s in self.segments
        ]
        colors = [self._bar_color(name) for name in names]
        fig = go.Figure(
            go.Bar(
                x=counts,
                y=names,
                orientation="h",
                text=labels,
                textposition="outside",
                cliponaxis=False,
                marker_color=colors,
                textfont={"size": 11, "color": "#475569"},
                hovertemplate="%{y}<br>%{x} customers<extra></extra>",
            )
        )
        fig.update_layout(
            height=max(320, 44 * len(names)),
            autosize=True,
            margin={"l": 10, "r": 130, "t": 10, "b": 35},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            showlegend=False,
            bargap=0.35,
            xaxis={"gridcolor": GRID, "zerolinecolor": GRID, "title": ""},
            yaxis={"autorange": "reversed", "showgrid": False, "title": ""},
        )
        self.segment_figure = fig

    def _build_revenue_figure(self) -> None:
        if not self.segments:
            self.segment_revenue_figure = _blank_figure(
                "No revenue contribution yet"
            )
            return
        ranked = sorted(self.segments, key=lambda s: s["revenue"], reverse=True)
        names = [s["name"] for s in ranked]
        revenues = [_safe_float(s["revenue"]) for s in ranked]
        labels = [
            f"{s['revenue_display']} · {s['revenue_share_display']}"
            for s in ranked
        ]
        colors = [self._bar_color(name) for name in names]
        fig = go.Figure(
            go.Bar(
                x=revenues,
                y=names,
                orientation="h",
                text=labels,
                textposition="outside",
                cliponaxis=False,
                marker_color=colors,
                textfont={"size": 11, "color": "#475569"},
                hovertemplate="%{y}<br>$%{x:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=max(320, 44 * len(names)),
            autosize=True,
            margin={"l": 10, "r": 150, "t": 10, "b": 35},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            showlegend=False,
            bargap=0.35,
            xaxis={
                "gridcolor": GRID,
                "zerolinecolor": GRID,
                "tickprefix": "$",
                "title": "",
            },
            yaxis={"autorange": "reversed", "showgrid": False, "title": ""},
        )
        self.segment_revenue_figure = fig

    def _bar_color(self, name: str) -> str:
        """Fade non-selected segments so the segment filter is visible in charts."""
        if self.selected_segment == ALL_SEGMENTS:
            return INDIGO
        return INDIGO if name == self.selected_segment else FADED

    def _build_summary(self) -> None:
        points: list[str] = [
            f"{self.customer_total:,} customers were scored from {self.rows_used:,} cleaned rows "
            f"totalling {self.total_revenue_display}.",
            f"Recency is counted from the latest valid transaction date in your file "
            f"({self.reference_date}); frequency uses {self.frequency_basis.lower()}; "
            "monetary value is total historical revenue per customer.",
            f"The average customer last ordered {self.avg_recency:,} days ago, "
            f"has {self.avg_frequency_display} orders and has spent {self.avg_monetary_display}.",
        ]
        if self.scoring_note:
            points.append(self.scoring_note)
        if self.top_segment:
            points.append(
                f"“{self.top_segment}” is the biggest segment with {self.top_segment_customers:,} customers."
            )
        if self.top_revenue_segment:
            points.append(
                f"“{self.top_revenue_segment}” brings in the most money at "
                f"{self.top_revenue_segment_display} ({self.top_revenue_segment_share} of revenue)."
            )
        if self.champion_customers:
            points.append(
                f"{self.champion_customers:,} Champions account for {self.champion_revenue_display} "
                f"({self.champion_revenue_share}) of revenue."
            )
        if self.loyal_customers or self.potential_loyalists:
            points.append(
                f"{self.loyal_customers:,} Loyal Customers and {self.potential_loyalists:,} "
                "Potential Loyalists sit just below the Champion tier."
            )
        if self.new_customers:
            points.append(
                f"{self.new_customers:,} New Customers bought very recently but not often yet."
            )
        if self.at_risk_customers:
            points.append(
                f"{self.at_risk_customers:,} customers are At Risk, holding "
                f"{self.at_risk_revenue_display} of historical revenue."
            )
        if self.cannot_lose_customers:
            points.append(
                f"{self.cannot_lose_customers:,} customers fall in “Cannot Lose Them”, holding "
                f"{self.cannot_lose_revenue_display} of historical revenue from high past "
                "frequency and spend."
            )
        if self.inactive_customers:
            points.append(
                f"{self.inactive_customers:,} customers sit in “Potentially Inactive”, holding "
                f"{self.inactive_revenue_display} of historical revenue. This is a segment label "
                "based on their own rows, not a prediction of future revenue loss."
            )
        if self.rows_skipped:
            points.append(
                f"{self.rows_skipped:,} row(s) were skipped because they lacked a customer, a readable date or a numeric amount."
            )
        self.summary_points = points

    def _insight(
        self,
        key: str,
        label: str,
        value: str,
        detail: str,
        icon: str,
        tone: str,
    ) -> RFMInsight:
        return RFMInsight(
            key=key,
            label=label,
            value=value,
            detail=detail,
            icon=icon,
            tone=tone,
        )

    def _build_insights(self, total_revenue: float) -> None:
        """Insights and recommendations written only from the values just calculated."""
        insights: list[RFMInsight] = []
        present = {segment["name"]: segment for segment in self.segments}
        total = max(0, int(self.customer_total))

        insights.append(
            self._insight(
                "scored",
                "Customers scored",
                f"{total:,}",
                f"Scored from {self.rows_used:,} usable row(s) worth "
                f"{self.total_revenue_display}, using the latest valid transaction date "
                f"({self.reference_date}) as the reference point.",
                "users-round",
                "info",
            )
        )

        if self.champion_customers:
            insights.append(
                self._insight(
                    "champions",
                    "Champions",
                    f"{self.champion_customers:,} customers",
                    f"They generate {self.champion_revenue_display}, which is "
                    f"{self.champion_revenue_share} of the "
                    f"{self.total_revenue_display} scored here — "
                    f"{_safe_div(self.champion_customers, max(1, total)) * 100:.1f}% of your "
                    "customers producing that share.",
                    "crown",
                    "good",
                )
            )
        else:
            insights.append(
                self._insight(
                    "champions",
                    "Champions",
                    "None found",
                    "No customer scored highly on recency together with frequency and "
                    "monetary value in this selection.",
                    "crown",
                    "info",
                )
            )

        if self.loyal_customers:
            insights.append(
                self._insight(
                    "loyal",
                    "Loyal Customers",
                    f"{self.loyal_customers:,} customers",
                    f"They hold {self.loyal_revenue_display} of historical revenue and are the "
                    "nearest group to Champion behaviour.",
                    "heart",
                    "good",
                )
            )

        at_risk_rows = [
            row
            for row in self.customers
            if row["segment"] in ("At Risk", "Cannot Lose Them")
        ]
        if at_risk_rows:
            ranked = sorted(
                at_risk_rows, key=lambda r: r["monetary"], reverse=True
            )
            top = ranked[0]
            at_risk_value = sum(row["monetary"] for row in at_risk_rows)
            insights.append(
                self._insight(
                    "at_risk_value",
                    "High-value customers slowing down",
                    f"{len(at_risk_rows):,} customers",
                    f"“At Risk” and “Cannot Lose Them” together hold {money(at_risk_value)} "
                    f"({_safe_div(at_risk_value, total_revenue) * 100:.1f}% of scored revenue). "
                    f"The largest is {top['name']} at {top['monetary_display']}, last ordering "
                    f"{top['last_order']} ({top['recency']:,} days before the reference date).",
                    "triangle-alert",
                    "warn",
                )
            )

        if self.inactive_customers:
            inactive_rows = sorted(
                [
                    row
                    for row in self.customers
                    if row["segment"] == "Potentially Inactive"
                ],
                key=lambda r: r["monetary"],
                reverse=True,
            )
            largest = (
                f" The largest is {inactive_rows[0]['name']} at "
                f"{inactive_rows[0]['monetary_display']}."
                if inactive_rows
                else ""
            )
            insights.append(
                self._insight(
                    "inactive",
                    "Potentially Inactive",
                    f"{self.inactive_customers:,} customers",
                    f"They hold {self.inactive_revenue_display} of historical revenue with no "
                    "recent purchase and low frequency or spend. This is a segment label from "
                    f"your own rows, not a prediction of future revenue loss.{largest}",
                    "moon",
                    "risk",
                )
            )

        if self.top_revenue_segment:
            insights.append(
                self._insight(
                    "revenue_leader",
                    "Largest revenue segment",
                    self.top_revenue_segment,
                    f"{self.top_revenue_segment} contributes "
                    f"{self.top_revenue_segment_display} "
                    f"({self.top_revenue_segment_share}) of the revenue scored here.",
                    "chart-pie",
                    "info",
                )
            )

        insights.append(
            self._insight(
                "averages",
                "Average customer profile",
                f"{self.avg_recency:,} days · {self.avg_frequency_display} orders",
                f"The median customer last ordered {self.median_recency:,} days ago and the "
                f"average customer has spent {self.avg_monetary_display}. Frequency uses "
                f"{self.frequency_basis.lower()}.",
                "activity",
                "info",
            )
        )

        recommendations: list[RFMRecommendation] = []
        for name in SEGMENT_ORDER:
            segment = present.get(name)
            action = RECOMMENDED_ACTIONS.get(name)
            if segment is None or action is None:
                continue
            title, detail, priority, icon = action
            recommendations.append(
                RFMRecommendation(
                    key=f"rec-{name.lower().replace(' ', '-')}",
                    segment=name,
                    title=title,
                    detail=detail,
                    priority=priority,
                    icon=icon,
                    scope=(
                        f"{segment['customers']:,} customer(s) · "
                        f"{segment['revenue_display']} "
                        f"({segment['revenue_share_display']} of scored revenue)"
                    ),
                )
            )

        self.insights = insights
        self.recommendations = recommendations
