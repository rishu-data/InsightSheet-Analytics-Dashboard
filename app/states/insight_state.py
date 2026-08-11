"""Automated insights and recommended actions.

Every insight is derived only from values calculated from the uploaded and
cleaned rows (respecting the dashboard filters). Nothing is estimated,
forecast or invented — if the data can't support a statement, it isn't shown.
"""

import logging
from typing import TypedDict

import pandas as pd
import reflex as rx

from app.states.dashboard_state import (
    _col,
    _safe_float,
    _short,
    _to_datetime,
    _to_number,
    money,
)

INACTIVE_DAYS = 60
MIN_SHARE_FOR_TREND = 1.0  # percent of total revenue an item must reach
UNUSUAL_SIGMA = 1.75


class Insight(TypedDict):
    key: str
    category: str
    title: str
    detail: str
    metric_label: str
    metric_value: str
    icon: str
    tone: str


class Suggestion(TypedDict):
    key: str
    title: str
    detail: str
    basis: str
    icon: str
    priority: str


def _pct_change(new: float, old: float) -> float:
    top = _safe_float(new)
    bottom = _safe_float(old)
    if bottom == 0:
        return 0.0
    return _safe_float((top - bottom) / abs(bottom) * 100)


def _signed(value: float) -> str:
    return f"{'+' if value > 0 else ''}{value:.1f}%"


class InsightState(rx.State):
    available: bool = False
    blocked_reason: str = "Upload a spreadsheet and map a date and revenue column to generate insights."
    missing_hints: list[str] = []

    insights: list[Insight] = []
    suggestions: list[Suggestion] = []

    rows_used: int = 0
    period_label: str = ""
    total_revenue_display: str = "$0.00"
    basis_note: str = ""

    @rx.var
    def insight_count(self) -> int:
        return len(self.insights)

    @rx.var
    def suggestion_count(self) -> int:
        return len(self.suggestions)

    @rx.var
    def positive_signals(self) -> int:
        return len([i for i in self.insights if i["tone"] == "good"])

    @rx.var
    def risk_signals(self) -> int:
        return len([i for i in self.insights if i["tone"] in ("warn", "bad")])

    @rx.var
    def has_insights(self) -> bool:
        return len(self.insights) > 0

    @rx.var
    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0

    @rx.event
    async def compute_insights(self):
        from app.states.filter_state import FilterState
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
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
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll read the patterns out of your own numbers.",
                [
                    "A date column",
                    "A revenue column",
                    "Optionally a customer and product column for richer insights",
                ],
            )
            return
        missing: list[str] = []
        if not _col(mapping, "date"):
            missing.append("A date column")
        if not _col(mapping, "revenue"):
            missing.append("A revenue column")
        if missing:
            self._unavailable(
                "Automated insights need a date and a revenue column. Map them on the upload page to unlock this tab.",
                missing,
            )
            return
        try:
            self._build(records, mapping, selections, dim_columns, start, end)
        except Exception as e:
            logging.exception(f"Error generating automated insights: {e}")
            self._unavailable(
                "We couldn't read reliable patterns from those columns. Try mapping a different date or revenue column.",
                ["Readable dates and numeric revenue values on the same row"],
            )

    def _unavailable(self, reason: str, hints: list[str]) -> None:
        self.available = False
        self.blocked_reason = reason
        self.missing_hints = hints
        self.insights = []
        self.suggestions = []
        self.rows_used = 0
        self.period_label = ""
        self.total_revenue_display = "$0.00"
        self.basis_note = ""

    def _build(
        self,
        records: list[dict[str, str]],
        mapping: dict[str, str],
        selections: dict[str, str],
        dim_columns: dict[str, str],
        start: str,
        end: str,
    ) -> None:
        selections = selections if isinstance(selections, dict) else {}
        dim_columns = dim_columns if isinstance(dim_columns, dict) else {}
        start = str(start or "").strip()
        end = str(end or "").strip()
        if not records:
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll read the patterns out of your own numbers.",
                [
                    "A date column",
                    "A revenue column",
                    "Optionally a customer and product column for richer insights",
                ],
            )
            return
        date_col = _col(mapping, "date")
        rev_col = _col(mapping, "revenue")
        cust_col = _col(mapping, "customer")
        prod_col = _col(mapping, "product")
        if not date_col or not rev_col:
            missing_cols: list[str] = []
            if not date_col:
                missing_cols.append("A date column")
            if not rev_col:
                missing_cols.append("A revenue column")
            self._unavailable(
                "Automated insights need a date and a revenue column. Map them on the upload page to unlock this tab.",
                missing_cols,
            )
            return

        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._unavailable(
                "There are no cleaned rows to read patterns from yet.",
                ["At least one row with a date and a revenue value"],
            )
            return
        if date_col not in df.columns or rev_col not in df.columns:
            self._unavailable(
                "The mapped columns are no longer in the cleaned file. Re-check your mapping on the upload page.",
                ["Date and revenue columns that exist in the file"],
            )
            return

        df["_date"] = _to_datetime(df[date_col])
        df["_rev"] = _to_number(df[rev_col])
        df = df.dropna(subset=["_date", "_rev"])
        if df.empty:
            self._unavailable(
                "None of the rows had both a readable date and a numeric revenue value, so no pattern can be measured.",
                ["Readable dates and numeric revenue values on the same row"],
            )
            return

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
            self._unavailable(
                "No rows match the filters you've chosen, so there is nothing to read patterns from. Widen the date range or clear a filter.",
                [],
            )
            return

        self.rows_used = int(len(df))
        total = _safe_float(df["_rev"].sum())
        self.total_revenue_display = money(total)
        self.period_label = (
            f"{df['_date'].min().strftime('%b %d, %Y')} → "
            f"{df['_date'].max().strftime('%b %d, %Y')}"
        )
        filter_note = (
            f" · {applied} filter(s) applied" if applied else " · no filters"
        )
        self.basis_note = (
            f"Read from {self.rows_used:,} cleaned rows worth "
            f"{self.total_revenue_display}{filter_note}."
        )

        insights: list[Insight] = []
        suggestions: list[Suggestion] = []

        self._revenue_insights(df, total, insights, suggestions)
        if prod_col and prod_col in df.columns:
            self._item_insights(
                df, prod_col, total, "product", insights, suggestions
            )
        if cust_col and cust_col in df.columns:
            self._customer_insights(df, cust_col, total, insights, suggestions)
        elif prod_col and prod_col in df.columns:
            self._concentration_insight(
                df, prod_col, total, "product", insights, suggestions
            )

        if not insights:
            insights.append(
                Insight(
                    key="baseline",
                    category="Baseline",
                    title="Not enough history for a trend yet",
                    detail=(
                        f"All {self.rows_used:,} rows in this selection total "
                        f"{self.total_revenue_display}, but they don't span enough time "
                        "or enough columns to compare anything against."
                    ),
                    metric_label="Rows analysed",
                    metric_value=f"{self.rows_used:,}",
                    icon="info",
                    tone="info",
                )
            )
        if not suggestions:
            suggestions.append(
                Suggestion(
                    key="map_more",
                    title="Map more columns for deeper insights",
                    detail=(
                        "Adding a customer and product column on the upload page lets us detect "
                        "growing and declining lines, high-value customers and churn risk."
                    ),
                    basis="Detected: only date and revenue are mapped for this dataset.",
                    icon="columns-3",
                    priority="Low",
                )
            )

        self.insights = insights
        self.suggestions = suggestions
        self.available = True
        self.blocked_reason = ""
        self.missing_hints = []

    # ---------------- revenue ----------------

    def _revenue_insights(
        self,
        df: pd.DataFrame,
        total: float,
        insights: list[Insight],
        suggestions: list[Suggestion],
    ) -> None:
        monthly = df.set_index("_date")["_rev"].resample("MS").sum()
        labels = [pd.Timestamp(i).strftime("%b %Y") for i in monthly.index]
        values = [_safe_float(v) for v in monthly.to_numpy()]
        if len(values) < 2:
            return

        last_date = df["_date"].max()
        last_stamp = pd.Timestamp(monthly.index[-1])
        complete = bool(
            last_date.normalize()
            >= (last_stamp + pd.offsets.MonthEnd(0)).normalize()
        )
        window = 0
        if complete:
            latest, prior = values[-1], values[-2]
            headline = "Month-over-month"
            basis = f"{labels[-1]} vs {labels[-2]} (complete months)"
            note = ""
        else:
            day = int(last_date.day)
            current_start = last_date.normalize().replace(day=1)
            previous_start = (
                current_start - pd.DateOffset(months=1)
            ).normalize()
            window = max(
                1, min(day, int(pd.Timestamp(previous_start).days_in_month))
            )
            previous_end = previous_start + pd.Timedelta(days=window - 1)
            latest = _safe_float(
                df[(df["_date"] >= current_start) & (df["_date"] <= last_date)][
                    "_rev"
                ].sum()
            )
            prior = _safe_float(
                df[
                    (df["_date"] >= previous_start)
                    & (df["_date"] < previous_end + pd.Timedelta(days=1))
                ]["_rev"].sum()
            )
            headline = "Month-to-Date"
            basis = (
                f"{labels[-1]} days 1\u2013{window} vs "
                f"{labels[-2]} days 1\u2013{window}"
            )
            note = (
                f" {labels[-1]} is still in progress (data ends "
                f"{last_date.strftime('%b %d, %Y')}), so only the first {window} "
                "day(s) of each month are compared."
            )
        change = _pct_change(latest, prior)
        rising = change > 0
        insights.append(
            Insight(
                key="mom",
                category=f"{headline} revenue",
                title=(
                    f"{headline} revenue rose in {labels[-1]}"
                    if rising
                    else (
                        f"{headline} revenue fell in {labels[-1]}"
                        if change < 0
                        else f"{headline} revenue held flat in {labels[-1]}"
                    )
                ),
                detail=(
                    f"{basis}: {money(latest)} against {money(prior)} — a difference of "
                    f"{money(abs(latest - prior))}.{note}"
                ),
                metric_label=basis,
                metric_value=_signed(change),
                icon="trending-up" if rising else "trending-down",
                tone="good" if rising else ("bad" if change < 0 else "info"),
            )
        )
        if abs(change) > 30:
            suggestions.append(
                Suggestion(
                    key="verify_large_change",
                    title="Verify data completeness before acting on this change",
                    detail=(
                        f"{headline} revenue moved {_signed(change)}, which is a large swing. "
                        "Check record counts, missing dates or amounts, duplicates and whether "
                        "the latest period is complete before treating it as a settled trend."
                    ),
                    basis=f"Detected: {basis} changed {_signed(change)}.",
                    icon="shield-check",
                    priority="High",
                )
            )
        if change <= -10:
            suggestions.append(
                Suggestion(
                    key="revenue_drop",
                    title="Review what changed last month",
                    detail=(
                        "Compare the products, customers and regions behind "
                        f"{labels[-1]} with {labels[-2]} to find where the "
                        f"{money(abs(latest - prior))} shortfall came from."
                    ),
                    basis=f"Detected: {headline.lower()} revenue fell {abs(change):.1f}% ({basis}).",
                    icon="search",
                    priority="High",
                )
            )
        elif change >= 10:
            suggestions.append(
                Suggestion(
                    key="revenue_rise",
                    title="Double down on what worked",
                    detail=(
                        f"{labels[-1]} outperformed {labels[-2]} by {money(latest - prior)}. "
                        "Identify the lines and accounts responsible and repeat the same play."
                    ),
                    basis=f"Detected: {headline.lower()} revenue rose {change:.1f}% ({basis}).",
                    icon="rocket",
                    priority="Medium",
                )
            )

        best_idx = values.index(max(values))
        worst_idx = values.index(min(values))
        average = sum(values) / len(values) if values else 0.0
        insights.append(
            Insight(
                key="best_month",
                category="Seasonality",
                title=f"{labels[best_idx]} was the strongest month",
                detail=(
                    f"{labels[best_idx]} brought in {money(values[best_idx])}, "
                    f"{_signed(_pct_change(values[best_idx], average))} against the "
                    f"{money(average)} monthly average across {len(values)} months."
                ),
                metric_label="Strongest month",
                metric_value=money(values[best_idx]),
                icon="award",
                tone="good",
            )
        )
        if worst_idx != best_idx:
            insights.append(
                Insight(
                    key="worst_month",
                    category="Seasonality",
                    title=f"{labels[worst_idx]} was the weakest month",
                    detail=(
                        f"{labels[worst_idx]} produced {money(values[worst_idx])}, "
                        f"{_signed(_pct_change(values[worst_idx], average))} against the "
                        f"{money(average)} monthly average."
                    ),
                    metric_label="Weakest month",
                    metric_value=money(values[worst_idx]),
                    icon="trending-down",
                    tone="warn",
                )
            )
            suggestions.append(
                Suggestion(
                    key="seasonality",
                    title="Plan around your quiet months",
                    detail=(
                        f"{labels[worst_idx]} is your softest month in this range while "
                        f"{labels[best_idx]} is the strongest. Shift campaigns and stock toward the pattern you already have."
                    ),
                    basis=(
                        f"Detected: {money(values[best_idx])} in {labels[best_idx]} versus "
                        f"{money(values[worst_idx])} in {labels[worst_idx]}."
                    ),
                    icon="calendar-range",
                    priority="Medium",
                )
            )

        if len(values) >= 4:
            series = pd.Series(values)
            std = _safe_float(series.std())
            mean = _safe_float(series.mean())
            if std > 0:
                deviations = [
                    (abs(v - mean) / std, i) for i, v in enumerate(values)
                ]
                score, index = max(deviations, key=lambda item: item[0])
                if score >= UNUSUAL_SIGMA:
                    above = values[index] > mean
                    insights.append(
                        Insight(
                            key="unusual",
                            category="Anomaly",
                            title=f"{labels[index]} looks unusual",
                            detail=(
                                f"{labels[index]} recorded {money(values[index])}, which is "
                                f"{score:.1f} standard deviations "
                                f"{'above' if above else 'below'} the {money(mean)} monthly average. "
                                "Worth checking whether that month is real or a data issue."
                            ),
                            metric_label="Deviation from average",
                            metric_value=f"{score:.1f}σ",
                            icon="activity",
                            tone="warn",
                        )
                    )
                    suggestions.append(
                        Suggestion(
                            key="verify_anomaly",
                            title=f"Verify the {labels[index]} figures",
                            detail=(
                                f"{labels[index]} sits far outside your normal range. Confirm the export "
                                "for that month is complete and free of duplicated or one-off lines."
                            ),
                            basis=(
                                f"Detected: {money(values[index])} in {labels[index]} vs a "
                                f"{money(mean)} average ({score:.1f}σ)."
                            ),
                            icon="shield-check",
                            priority="Medium",
                        )
                    )

        if len(values) >= 4:
            half = len(values) // 2
            first_half = sum(values[:half])
            second_half = sum(values[half:])
            direction = _pct_change(second_half, first_half)
            insights.append(
                Insight(
                    key="half_trend",
                    category="Revenue trend",
                    title=(
                        "The second half of this period is stronger"
                        if direction > 0
                        else "The second half of this period is weaker"
                    ),
                    detail=(
                        f"{labels[half]}–{labels[-1]} totals {money(second_half)} against "
                        f"{money(first_half)} for {labels[0]}–{labels[half - 1]}."
                    ),
                    metric_label="Second half vs first half",
                    metric_value=_signed(direction),
                    icon="chart-line",
                    tone="good" if direction > 0 else "warn",
                )
            )

    # ---------------- products ----------------

    def _item_insights(
        self,
        df: pd.DataFrame,
        column: str,
        total: float,
        kind: str,
        insights: list[Insight],
        suggestions: list[Suggestion],
    ) -> None:
        work = df.assign(
            _key=df[column].astype(str).str.strip().replace("", "(blank)")
        )
        totals = work.groupby("_key")["_rev"].sum().sort_values(ascending=False)
        if totals.empty:
            return

        leader = str(totals.index[0])
        leader_value = _safe_float(totals.iloc[0])
        leader_share = (
            leader_value / total * 100 if total not in (0, 0.0) else 0.0
        )
        insights.append(
            Insight(
                key="top_product",
                category="Product mix",
                title=f"{_short(leader, 34)} leads your {kind} mix",
                detail=(
                    f"{_short(leader, 34)} generated {money(leader_value)} of "
                    f"{money(total)}, the largest single {kind} in this selection "
                    f"({int(totals.size)} {kind}s in total)."
                ),
                metric_label="Share of revenue",
                metric_value=f"{leader_share:.1f}%",
                icon="package",
                tone="info",
            )
        )
        if leader_share >= 40:
            suggestions.append(
                Suggestion(
                    key="product_concentration",
                    title=f"Reduce reliance on one {kind}",
                    detail=(
                        f"{_short(leader, 34)} alone carries {leader_share:.1f}% of revenue. "
                        f"Growing the next two or three {kind}s would spread that risk."
                    ),
                    basis=f"Detected: {money(leader_value)} of {money(total)} from a single {kind}.",
                    icon="shuffle",
                    priority="Medium",
                )
            )

        span = df["_date"].max() - df["_date"].min()
        if span < pd.Timedelta(days=45):
            return
        mid = df["_date"].min() + span / 2
        first = work[work["_date"] < mid].groupby("_key")["_rev"].sum()
        second = work[work["_date"] >= mid].groupby("_key")["_rev"].sum()
        frame = pd.concat(
            [first.rename("first"), second.rename("second")], axis=1
        ).fillna(0.0)
        frame["total"] = frame["first"] + frame["second"]
        floor = abs(total) * MIN_SHARE_FOR_TREND / 100
        frame = frame[(frame["total"] >= floor) & (frame["first"] > 0)]
        if frame.empty:
            return
        frame["change"] = (
            (frame["second"] - frame["first"]) / frame["first"] * 100
        )
        frame = frame.sort_values("change", ascending=False)

        first_label = (
            f"{df['_date'].min().strftime('%b %Y')}–{mid.strftime('%b %Y')}"
        )
        second_label = (
            f"{mid.strftime('%b %Y')}–{df['_date'].max().strftime('%b %Y')}"
        )

        top = frame.iloc[0]
        if float(top["change"]) > 5:
            name = _short(frame.index[0], 34)
            insights.append(
                Insight(
                    key="fast_growing",
                    category="Growth",
                    title=f"{name} is your fastest-growing {kind}",
                    detail=(
                        f"{name} moved from {money(float(top['first']))} in {first_label} to "
                        f"{money(float(top['second']))} in {second_label}."
                    ),
                    metric_label="Half-over-half growth",
                    metric_value=_signed(float(top["change"])),
                    icon="trending-up",
                    tone="good",
                )
            )
            suggestions.append(
                Suggestion(
                    key="push_growth",
                    title=f"Give {name} more room to run",
                    detail=(
                        f"{name} is growing faster than anything else in your file. "
                        "Consider prioritising stock, pricing tests or promotion behind it."
                    ),
                    basis=(
                        f"Detected: {money(float(top['first']))} → {money(float(top['second']))} "
                        f"({_signed(float(top['change']))})."
                    ),
                    icon="rocket",
                    priority="High",
                )
            )

        bottom = frame.iloc[-1]
        if float(bottom["change"]) < -5:
            name = _short(frame.index[-1], 34)
            insights.append(
                Insight(
                    key="declining",
                    category="Growth",
                    title=f"{name} is declining",
                    detail=(
                        f"{name} slipped from {money(float(bottom['first']))} in {first_label} to "
                        f"{money(float(bottom['second']))} in {second_label}."
                    ),
                    metric_label="Half-over-half change",
                    metric_value=_signed(float(bottom["change"])),
                    icon="trending-down",
                    tone="bad",
                )
            )
            suggestions.append(
                Suggestion(
                    key="fix_decline",
                    title=f"Investigate the drop in {name}",
                    detail=(
                        f"{name} lost {money(float(bottom['first']) - float(bottom['second']))} "
                        "between the two halves of this period. Check pricing, availability "
                        "and whether specific customers stopped buying it."
                    ),
                    basis=(
                        f"Detected: {money(float(bottom['first']))} → "
                        f"{money(float(bottom['second']))} ({_signed(float(bottom['change']))})."
                    ),
                    icon="wrench",
                    priority="High",
                )
            )

    # ---------------- customers ----------------

    def _customer_insights(
        self,
        df: pd.DataFrame,
        column: str,
        total: float,
        insights: list[Insight],
        suggestions: list[Suggestion],
    ) -> None:
        reference = df["_date"].max()
        work = df.assign(
            _key=df[column].astype(str).str.strip().replace("", "(blank)")
        )
        grouped = work.groupby("_key").agg(
            revenue=("_rev", "sum"),
            orders=("_rev", "size"),
            last_order=("_date", "max"),
        )
        if grouped.empty:
            return
        grouped["days_since"] = (reference - grouped["last_order"]).dt.days
        grouped = grouped.sort_values("revenue", ascending=False)
        count = int(len(grouped))
        if count == 0:
            return

        leader = str(grouped.index[0])
        leader_value = _safe_float(grouped["revenue"].iloc[0])
        leader_share = (
            leader_value / total * 100 if total not in (0, 0.0) else 0.0
        )
        insights.append(
            Insight(
                key="top_customer",
                category="Customers",
                title=f"{_short(leader, 34)} is your highest-value customer",
                detail=(
                    f"{_short(leader, 34)} has spent {money(leader_value)} across "
                    f"{int(grouped['orders'].iloc[0]):,} row(s), the most of any of your "
                    f"{count:,} customers."
                ),
                metric_label="Share of revenue",
                metric_value=f"{leader_share:.1f}%",
                icon="crown",
                tone="good",
            )
        )

        top_five = grouped.head(5)
        five_share = (
            _safe_float(top_five["revenue"].sum()) / total * 100
            if total not in (0, 0.0)
            else 0.0
        )
        insights.append(
            Insight(
                key="top_five",
                category="Customers",
                title=f"Your top {int(len(top_five))} customers carry {five_share:.1f}% of revenue",
                detail=(
                    f"{money(float(top_five['revenue'].sum()))} of {money(total)} comes from just "
                    f"{int(len(top_five))} of {count:,} customers."
                ),
                metric_label="Top 5 revenue",
                metric_value=money(float(top_five["revenue"].sum())),
                icon="users-round",
                tone="info" if five_share < 60 else "warn",
            )
        )

        cumulative = grouped["revenue"].cumsum()
        half = total / 2 if total not in (0, 0.0) else 0.0
        needed = (
            int((cumulative < half).sum()) + 1 if total not in (0, 0.0) else 0
        )
        needed = min(max(needed, 1), count)
        needed_share = needed / count * 100 if count else 0.0
        insights.append(
            Insight(
                key="concentration",
                category="Concentration",
                title=f"{needed:,} customer(s) make up half your revenue",
                detail=(
                    f"{needed:,} of {count:,} customers ({needed_share:.1f}%) account for the first "
                    f"{money(half)} of {money(total)} — the rest is spread across the remainder."
                ),
                metric_label="Customers for 50% of revenue",
                metric_value=f"{needed_share:.1f}% of accounts",
                icon="chart-pie",
                tone="warn" if needed_share <= 20 else "info",
            )
        )
        if needed_share <= 20:
            suggestions.append(
                Suggestion(
                    key="diversify",
                    title="Protect and broaden the revenue base",
                    detail=(
                        f"Half of all revenue sits with {needed:,} account(s). A retention plan for those "
                        "accounts plus growth targets for mid-tier customers would lower the risk."
                    ),
                    basis=(
                        f"Detected: {needed:,} of {count:,} customers ({needed_share:.1f}%) reach "
                        f"{money(half)} of {money(total)}."
                    ),
                    icon="shield",
                    priority="High",
                )
            )

        inactive = grouped[grouped["days_since"] >= INACTIVE_DAYS]
        if not inactive.empty:
            lost_value = _safe_float(inactive["revenue"].sum())
            biggest = inactive.sort_values("revenue", ascending=False).iloc[0]
            biggest_name = _short(
                inactive.sort_values("revenue", ascending=False).index[0], 34
            )
            insights.append(
                Insight(
                    key="at_risk",
                    category="Potentially inactive customers",
                    title=f"{int(len(inactive)):,} potentially inactive customer(s)",
                    detail=(
                        f"They haven't appeared in {INACTIVE_DAYS}+ days as of "
                        f"{reference.strftime('%b %d, %Y')}. Historical revenue associated with them "
                        f"totals {money(lost_value)} — this is not a prediction of future revenue loss. "
                        f"The largest is {biggest_name} at {money(float(biggest['revenue']))}, "
                        f"last seen {int(biggest['days_since']):,} days ago."
                    ),
                    metric_label="Historical revenue from potentially inactive customers",
                    metric_value=money(lost_value),
                    icon="user-x",
                    tone="bad",
                )
            )
            suggestions.append(
                Suggestion(
                    key="winback",
                    title="Run a win-back on the quiet accounts",
                    detail=(
                        f"Start with {biggest_name} and the other {max(0, int(len(inactive)) - 1):,} "
                        f"account(s) that have been silent for {INACTIVE_DAYS}+ days — they have already bought before."
                    ),
                    basis=(
                        f"Detected: {int(len(inactive)):,} potentially inactive customers "
                        f"({INACTIVE_DAYS}+ days), holding {money(lost_value)} of historical revenue."
                    ),
                    icon="mail",
                    priority="High",
                )
            )
            ranges: list[tuple[str, int, int | None]] = [
                ("60\u201390 days", 60, 90),
                ("91\u2013180 days", 91, 180),
                ("181\u2013365 days", 181, 365),
                ("365+ days", 366, None),
            ]
            parts: list[str] = []
            for label, low, high in ranges:
                block = (
                    inactive[inactive["days_since"] >= low]
                    if high is None
                    else inactive[
                        (inactive["days_since"] >= low)
                        & (inactive["days_since"] <= high)
                    ]
                )
                if len(block):
                    parts.append(
                        f"{label}: {int(len(block)):,} customer(s), "
                        f"{money(_safe_float(block['revenue'].sum()))}"
                    )
            if parts:
                insights.append(
                    Insight(
                        key="inactivity_buckets",
                        category="Potentially inactive customers",
                        title="How long your inactive customers have been quiet",
                        detail=(
                            " · ".join(parts)
                            + ". These are historical revenue figures for customers inactive "
                            f"{INACTIVE_DAYS}+ days, not a prediction of future revenue loss."
                        ),
                        metric_label="Longest-quiet band",
                        metric_value=parts[-1].split(":")[0],
                        icon="hourglass",
                        tone="warn",
                    )
                )

        repeat = grouped[grouped["orders"] > 1]
        repeat_rate = len(repeat) / count * 100 if count else 0.0
        insights.append(
            Insight(
                key="repeat",
                category="Customers",
                title=(
                    f"{repeat_rate:.1f}% of customers bought more than once"
                    if repeat_rate > 0
                    else "No customer appears more than once"
                ),
                detail=(
                    f"{int(len(repeat)):,} of {count:,} customers have more than one row in this selection, "
                    f"averaging {_safe_float(grouped['orders'].mean()):.1f} rows per customer."
                ),
                metric_label="Repeat rate",
                metric_value=f"{repeat_rate:.1f}%",
                icon="repeat",
                tone="good" if repeat_rate >= 30 else "warn",
            )
        )
        if repeat_rate < 30:
            suggestions.append(
                Suggestion(
                    key="repeat_push",
                    title="Build a second-purchase play",
                    detail=(
                        "Most customers in this file only appear once. A follow-up sequence after the "
                        "first order is the cheapest way to lift this rate."
                    ),
                    basis=f"Detected: repeat rate of {repeat_rate:.1f}% across {count:,} customers.",
                    icon="repeat",
                    priority="Medium",
                )
            )

    def _concentration_insight(
        self,
        df: pd.DataFrame,
        column: str,
        total: float,
        kind: str,
        insights: list[Insight],
        suggestions: list[Suggestion],
    ) -> None:
        totals = (
            df.assign(
                _key=df[column].astype(str).str.strip().replace("", "(blank)")
            )
            .groupby("_key")["_rev"]
            .sum()
            .sort_values(ascending=False)
        )
        if totals.empty:
            return
        count = int(totals.size)
        cumulative = totals.cumsum()
        half = total / 2 if total not in (0, 0.0) else 0.0
        needed = min(max(int((cumulative < half).sum()) + 1, 1), count)
        share = needed / count * 100 if count else 0.0
        insights.append(
            Insight(
                key="concentration",
                category="Concentration",
                title=f"{needed:,} {kind}(s) make up half your revenue",
                detail=(
                    f"{needed:,} of {count:,} {kind}s ({share:.1f}%) reach the first {money(half)} "
                    f"of {money(total)}. No customer column is mapped, so concentration is measured by {kind}."
                ),
                metric_label=f"{kind.title()}s for 50% of revenue",
                metric_value=f"{share:.1f}%",
                icon="chart-pie",
                tone="warn" if share <= 25 else "info",
            )
        )
