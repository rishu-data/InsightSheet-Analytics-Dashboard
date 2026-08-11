"""Ask InsightSheet — a deterministic, dataset-grounded question answerer.

Every answer is computed from the cleaned rows currently in view (the same rows
and filters the dashboard uses). No external model is called, no value is
estimated, and when the uploaded data cannot support an answer we say so.
"""

import logging
from typing import TypedDict

import pandas as pd
import reflex as rx

from app.states.dashboard_state import (
    _col,
    _safe_div,
    _safe_float,
    _short,
    _to_datetime,
    _to_number,
    money,
)

CANT_ANSWER = "I can't answer that from the uploaded dataset."
INACTIVE_DAYS = 60

_REGION_WORDS: tuple[str, ...] = (
    "region",
    "country",
    "state",
    "province",
    "city",
    "territory",
    "market",
    "zone",
)


class ChatTurn(TypedDict):
    id: str
    question: str
    answer: str
    evidence: list[str]
    recommendation: str
    answered: bool
    topic: str


class ProfitFacts(TypedDict):
    available: bool
    profit: str
    margin: str
    cost: str
    cost_share: str
    per_order: str
    method: str
    best: str
    best_margin: str
    worst: str
    worst_margin: str
    loss_rows: int
    loss_amount: str


class SegmentFacts(TypedDict):
    available: bool
    customers: int
    top_segment: str
    top_segment_customers: int
    top_revenue_segment: str
    top_revenue_segment_display: str
    top_revenue_segment_share: str
    champion_customers: int
    champion_revenue_display: str
    champion_revenue_share: str
    at_risk_customers: int
    cannot_lose_customers: int
    inactive_customers: int
    reference_date: str


def _norm(name: object) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def _has(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _group(df: pd.DataFrame, column: str) -> pd.Series:
    work = df.assign(
        _key=df[column].astype(str).str.strip().replace("", "(blank)")
    )
    return work.groupby("_key")["_rev"].sum().sort_values(ascending=False)


def _find_region_column(df: pd.DataFrame, used: set[str]) -> str:
    for word in _REGION_WORDS:
        for col in df.columns:
            name = str(col)
            if name in used or name.startswith("_"):
                continue
            if word in _norm(name):
                unique = int(df[name].astype(str).str.strip().nunique())
                if 2 <= unique <= 60:
                    return name
    return ""


def _pct(value: float) -> str:
    return f"{'+' if value > 0 else ''}{value:.1f}%"


class AskState(rx.State):
    """Chat-style Q&A grounded in the uploaded dataset."""

    turns: list[ChatTurn] = []
    is_thinking: bool = False
    error_message: str = ""
    counter: int = 0

    ready: bool = False
    blocked_reason: str = "Upload a spreadsheet and map a date and revenue column to start asking questions."
    source_name: str = ""
    rows_available: int = 0
    has_customer: bool = False
    has_product: bool = False
    profit_ready: bool = False
    segments_ready: bool = False

    @rx.var
    def turn_count(self) -> int:
        return len(self.turns)

    @rx.var
    def answered_count(self) -> int:
        return len([turn for turn in self.turns if turn["answered"]])

    @rx.var
    def has_turns(self) -> bool:
        return len(self.turns) > 0

    @rx.var
    def suggestions(self) -> list[str]:
        items: list[str] = [
            "What was my total revenue?",
            "Is revenue growing or declining?",
            "Which month was strongest?",
        ]
        if self.has_customer:
            items.append("Who is my top customer?")
            items.append("Which customers are at risk?")
            items.append("How many customers are potentially inactive?")
            items.append("How concentrated is my customer revenue?")
            items.append("What is my repeat customer rate?")
        if self.has_product:
            items.append("Which product sells best?")
            items.append("Which product is weakest?")
        if self.profit_ready:
            items.append("What is my profit margin?")
        if self.segments_ready:
            items.append("Which customer segment matters most?")
            items.append("How many Champions do I have?")
        items.append("What is my average order value?")
        return items[:9]

    @rx.event
    async def prepare(self):
        """Refresh the availability flags used for suggestions and empty states."""
        from app.states.profit_state import ProfitState
        from app.states.rfm_state import RFMState
        from app.states.upload_state import UploadState

        try:
            upload = await self.get_state(UploadState)
            mapping = dict(upload.mapping or {})
            self.source_name = upload.file_name
            self.rows_available = int(upload.clean_rows)
            self.has_customer = bool(_col(mapping, "customer"))
            self.has_product = bool(_col(mapping, "product"))
            self.ready = bool(
                upload.clean_records
                and _col(mapping, "date")
                and _col(mapping, "revenue")
            )
            if not upload.clean_records:
                self.blocked_reason = (
                    "Upload a CSV or Excel export on the upload page and I'll answer "
                    "questions from the cleaned rows."
                )
            elif not self.ready:
                self.blocked_reason = (
                    "Map a date column and a revenue column on the upload page so I have "
                    "numbers to reason about."
                )
            else:
                self.blocked_reason = ""
            profit = await self.get_state(ProfitState)
            self.profit_ready = bool(profit.available)
            rfm = await self.get_state(RFMState)
            self.segments_ready = bool(rfm.available)
        except Exception as e:
            logging.exception(f"Error preparing Ask InsightSheet: {e}")
            self.ready = False
            self.blocked_reason = "Something went wrong reading your dataset. Re-upload the file and try again."

    @rx.event
    def clear_conversation(self):
        self.turns = []
        self.error_message = ""

    @rx.event
    async def submit(self, form_data: dict):
        text = str(form_data.get("question", "") or "")
        return AskState.ask(text)

    @rx.event
    async def ask(self, question: str):
        text = " ".join(str(question or "").split())
        if not text:
            self.error_message = (
                "Type a question first — for example “Is revenue growing?”."
            )
            return
        self.error_message = ""
        self.is_thinking = True
        yield
        try:
            turn = await self._build_turn(text)
        except Exception as e:
            logging.exception(f"Error answering “{text}”: {e}")
            turn = self._turn(
                text,
                CANT_ANSWER,
                [
                    "Something in the mapped columns couldn't be read as dates or numbers."
                ],
                "Re-check the date and revenue columns on the upload page, then ask again.",
                False,
                "error",
            )
        self.turns.append(turn)
        self.is_thinking = False

    def _turn(
        self,
        question: str,
        answer: str,
        evidence: list[str],
        recommendation: str,
        answered: bool,
        topic: str,
    ) -> ChatTurn:
        self.counter += 1
        return ChatTurn(
            id=f"turn-{self.counter}",
            question=question,
            answer=answer,
            evidence=evidence,
            recommendation=recommendation,
            answered=answered,
            topic=topic,
        )

    async def _build_turn(self, text: str) -> ChatTurn:
        from app.states.filter_state import FilterState
        from app.states.profit_state import ProfitState
        from app.states.rfm_state import RFMState
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        if not records:
            return self._turn(
                text,
                CANT_ANSWER,
                ["No spreadsheet has been uploaded in this session."],
                "Upload a sales export on the upload page, then ask me again.",
                False,
                "no_data",
            )
        if not _col(mapping, "date") or not _col(mapping, "revenue"):
            return self._turn(
                text,
                CANT_ANSWER,
                [
                    "A date column and a revenue column must be mapped before anything can be calculated."
                ],
                "Open the upload page and map the date and revenue columns.",
                False,
                "no_mapping",
            )

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

        df = self._frame(records, mapping, selections, dim_columns, start, end)
        if df is None or df.empty:
            return self._turn(
                text,
                CANT_ANSWER,
                [
                    "No cleaned row currently in view has both a readable date and a numeric amount."
                ],
                "Widen the date range or clear a filter on the dashboard, then ask again.",
                False,
                "no_rows",
            )

        profit = await self.get_state(ProfitState)
        profit_facts = ProfitFacts(
            available=bool(profit.available),
            profit=profit.total_profit_signed,
            margin=profit.margin_display,
            cost=profit.total_cost_display,
            cost_share=f"{profit.cost_share:.1f}%",
            per_order=profit.profit_per_order_display,
            method=profit.method_formula,
            best=profit.best_margin_name,
            best_margin=profit.best_margin_display,
            worst=profit.worst_margin_name,
            worst_margin=profit.worst_margin_display,
            loss_rows=int(profit.loss_rows),
            loss_amount=profit.loss_amount_display,
        )
        rfm = await self.get_state(RFMState)
        segment_facts = SegmentFacts(
            available=bool(rfm.available),
            customers=int(rfm.customer_total),
            top_segment=rfm.top_segment,
            top_segment_customers=int(rfm.top_segment_customers),
            top_revenue_segment=rfm.top_revenue_segment,
            top_revenue_segment_display=rfm.top_revenue_segment_display,
            top_revenue_segment_share=rfm.top_revenue_segment_share,
            champion_customers=int(rfm.champion_customers),
            champion_revenue_display=rfm.champion_revenue_display,
            champion_revenue_share=rfm.champion_revenue_share,
            at_risk_customers=int(rfm.at_risk_customers),
            cannot_lose_customers=int(rfm.cannot_lose_customers),
            inactive_customers=int(rfm.inactive_customers),
            reference_date=rfm.reference_date,
        )

        answer, evidence, recommendation, answered, topic = self._respond(
            text, df, mapping, profit_facts, segment_facts
        )
        return self._turn(
            text, answer, evidence, recommendation, answered, topic
        )

    def _frame(
        self,
        records: list[dict[str, str]],
        mapping: dict[str, str],
        selections: dict[str, str],
        dim_columns: dict[str, str],
        start: str,
        end: str,
    ) -> pd.DataFrame | None:
        date_col = _col(mapping, "date")
        rev_col = _col(mapping, "revenue")
        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            return None
        if date_col not in df.columns or rev_col not in df.columns:
            return None
        df["_date"] = _to_datetime(df[date_col])
        df["_rev"] = _to_number(df[rev_col])
        df = df.dropna(subset=["_date", "_rev"])
        if df.empty:
            return None
        start_stamp = pd.to_datetime(start, errors="coerce") if start else None
        end_stamp = pd.to_datetime(end, errors="coerce") if end else None
        if start_stamp is not None and not pd.isna(start_stamp):
            df = df[df["_date"] >= start_stamp]
        if end_stamp is not None and not pd.isna(end_stamp):
            df = df[df["_date"] < end_stamp + pd.Timedelta(days=1)]
        for key, value in selections.items():
            column = dim_columns.get(key, "")
            if not column or column not in df.columns:
                continue
            df = df[df[column].astype(str).str.strip() == value]
        return df

    # ------------------------------------------------------------------
    # answer routing
    # ------------------------------------------------------------------

    def _respond(
        self,
        text: str,
        df: pd.DataFrame,
        mapping: dict[str, str],
        profit: ProfitFacts,
        segments: SegmentFacts,
    ) -> tuple[str, list[str], str, bool, str]:
        q = text.lower()
        rows = int(len(df))
        total = _safe_float(df["_rev"].sum())
        start = df["_date"].min()
        end = df["_date"].max()
        period = f"{start.strftime('%b %d, %Y')} → {end.strftime('%b %d, %Y')}"
        basis = f"Calculated from {rows:,} cleaned rows covering {period}."

        cust_col = _col(mapping, "customer")
        prod_col = _col(mapping, "product")
        order_col = _col(mapping, "order_id")
        has_cust = bool(cust_col) and cust_col in df.columns
        has_prod = bool(prod_col) and prod_col in df.columns

        orders = rows
        order_note = (
            "Every cleaned row with a date and an amount counts as one order."
        )
        if order_col and order_col in df.columns:
            keys = df[order_col].astype(str).str.strip()
            distinct = int(keys[keys != ""].nunique())
            if distinct:
                orders = distinct
                order_note = f"Orders are the {distinct:,} distinct values in “{order_col}”."
        aov = _safe_div(total, orders)

        monthly = (
            df.set_index("_date")["_rev"].resample("MS").agg(["sum", "size"])
        )
        labels = [pd.Timestamp(i).strftime("%b %Y") for i in monthly.index]
        values = [_safe_float(v) for v in monthly["sum"].to_numpy()]
        counts = [int(v) for v in monthly["size"].to_numpy()]

        month_complete = True
        mtd_window = 0
        mtd_current = 0.0
        mtd_previous = 0.0
        if labels:
            last_stamp = pd.Timestamp(monthly.index[-1])
            month_complete = bool(
                end.normalize()
                >= (last_stamp + pd.offsets.MonthEnd(0)).normalize()
            )
            if not month_complete and len(labels) > 1:
                day = int(end.day)
                current_start = end.normalize().replace(day=1)
                previous_start = (
                    current_start - pd.DateOffset(months=1)
                ).normalize()
                mtd_window = max(
                    1,
                    min(day, int(pd.Timestamp(previous_start).days_in_month)),
                )
                previous_end = previous_start + pd.Timedelta(
                    days=mtd_window - 1
                )
                mtd_current = _safe_float(
                    df[(df["_date"] >= current_start) & (df["_date"] <= end)][
                        "_rev"
                    ].sum()
                )
                mtd_previous = _safe_float(
                    df[
                        (df["_date"] >= previous_start)
                        & (df["_date"] < previous_end + pd.Timedelta(days=1))
                    ]["_rev"].sum()
                )

        # ---------------- profit / margin / cost ----------------
        if _has(q, ("profit", "margin", "cost", "cogs", "expense")):
            if not profit["available"]:
                return (
                    CANT_ANSWER,
                    [
                        "No cost, profit, unit-cost or margin column was found in your file.",
                        "Profit is never estimated — it is only shown when your own data supports it.",
                    ],
                    "Add a cost or profit column to your export (or units sold with a unit cost) and upload it again.",
                    False,
                    "profit",
                )
            evidence = [
                f"Total profit is {profit['profit']} on {money(total)} of revenue.",
                f"Cost of sales is {profit['cost']} — {profit['cost_share']} of revenue.",
                f"Profit per order is {profit['per_order']} across {orders:,} orders.",
                f"Formula used: {profit['method']}.",
            ]
            if profit["best"]:
                evidence.append(
                    f"Best margin: {profit['best']} at {profit['best_margin']}; "
                    f"weakest: {profit['worst']} at {profit['worst_margin']}."
                )
            if profit["loss_rows"]:
                evidence.append(
                    f"{profit['loss_rows']:,} row(s) sold below cost, losing {profit['loss_amount']}."
                )
            recommendation = (
                f"Review the lowest-margin line ({profit['worst']} at {profit['worst_margin']}) before chasing more volume."
                if profit["worst"]
                else "Keep watching cost of sales as a share of revenue month by month."
            )
            return (
                f"Your overall profit margin is {profit['margin']}, worth {profit['profit']} of profit.",
                evidence,
                recommendation,
                True,
                "profit",
            )

        # ---------------- segments ----------------
        if _has(
            q,
            (
                "segment",
                "rfm",
                "champion",
                "vip",
                "loyal tier",
                "tier",
            ),
        ):
            if not segments["available"]:
                return (
                    CANT_ANSWER,
                    [
                        "RFM analysis is unavailable because the uploaded dataset does not "
                        "contain sufficient customer transaction information."
                    ],
                    "Map a customer, date and revenue column on the upload page to unlock RFM segments.",
                    False,
                    "segments",
                )
            evidence = [
                f"{segments['customers']:,} customers were scored on recency, frequency and "
                f"monetary value as of {segments['reference_date']}.",
                f"Biggest segment: {segments['top_segment']} with {segments['top_segment_customers']:,} customers.",
                f"{segments['top_revenue_segment']} contributes {segments['top_revenue_segment_display']} "
                f"({segments['top_revenue_segment_share']}) of revenue.",
                f"{segments['champion_customers']:,} Champions generate "
                f"{segments['champion_revenue_display']} ({segments['champion_revenue_share']}).",
                f"{segments['at_risk_customers']:,} customer(s) sit in “At Risk”, "
                f"{segments['cannot_lose_customers']:,} in “Cannot Lose Them” and "
                f"{segments['inactive_customers']:,} in “Potentially Inactive” — segment labels "
                "scored from your own rows, not a prediction of future revenue loss.",
            ]
            return (
                f"“{segments['top_revenue_segment']}” matters most — it brings in "
                f"{segments['top_revenue_segment_display']} ({segments['top_revenue_segment_share']}) of revenue.",
                evidence,
                f"Recommendation: protect the {segments['champion_customers']:,} Champion account(s) "
                f"first, then re-engage the {segments['at_risk_customers']:,} At Risk and "
                f"{segments['cannot_lose_customers']:,} Cannot Lose Them customer(s).",
                True,
                "segments",
            )

        # ---------------- customers ----------------
        customer_words = (
            "customer",
            "client",
            "buyer",
            "account",
            "churn",
            "inactive",
            "repeat",
            "retention",
            "loyal",
            "at risk",
            "risk",
            "quiet",
            "dormant",
            "stopped",
            "lost",
        )
        if _has(q, customer_words):
            if not has_cust:
                return (
                    CANT_ANSWER,
                    [
                        "No customer column is mapped, so nothing can be grouped per customer."
                    ],
                    "Map a customer column (name, email or ID) on the upload page.",
                    False,
                    "customers",
                )
            work = df.assign(
                _key=df[cust_col].astype(str).str.strip().replace("", "(blank)")
            )
            grouped = work.groupby("_key").agg(
                revenue=("_rev", "sum"),
                rows=("_rev", "size"),
                last_order=("_date", "max"),
            )
            if grouped.empty:
                return (
                    CANT_ANSWER,
                    ["The mapped customer column had no usable values."],
                    "Check the customer column in your export and upload it again.",
                    False,
                    "customers",
                )
            grouped["days_since"] = (end - grouped["last_order"]).dt.days
            count = int(len(grouped))
            ranked = grouped.sort_values("revenue", ascending=False)
            leader = _short(ranked.index[0], 40)
            leader_value = _safe_float(ranked["revenue"].iloc[0])
            leader_share = _safe_div(leader_value, total) * 100
            inactive = grouped[grouped["days_since"] >= INACTIVE_DAYS]
            repeat = grouped[grouped["rows"] > 1]
            repeat_rate = _safe_div(len(repeat), count) * 100
            retention = _safe_div(count - len(inactive), count) * 100

            if _has(
                q,
                (
                    "inactive",
                    "churn",
                    "quiet",
                    "lost",
                    "stopped",
                    "at risk",
                    "risk",
                    "dormant",
                    "silent",
                    "lapsed",
                ),
            ):
                if inactive.empty:
                    return (
                        f"No customer is potentially inactive — every one of your {count:,} customers ordered within the last {INACTIVE_DAYS} days, so no historical revenue sits with quiet accounts.",
                        [
                            basis,
                            "Potentially inactive means no order for "
                            f"{INACTIVE_DAYS}+ days. It is not a prediction of future revenue loss.",
                            f"Days are counted from the newest date in view ({end.strftime('%b %d, %Y')}).",
                            f"Retention rate is {retention:.1f}%.",
                        ],
                        "Keep the current follow-up cadence — nothing is at churn risk in this selection.",
                        True,
                        "churn",
                    )
                lost_value = _safe_float(inactive["revenue"].sum())
                biggest = inactive.sort_values("revenue", ascending=False)
                bucket_lines: list[str] = []
                for label, low, high in (
                    ("60\u201390 days", 60, 90),
                    ("91\u2013180 days", 91, 180),
                    ("181\u2013365 days", 181, 365),
                    ("365+ days", 366, None),
                ):
                    block = (
                        inactive[inactive["days_since"] >= low]
                        if high is None
                        else inactive[
                            (inactive["days_since"] >= low)
                            & (inactive["days_since"] <= high)
                        ]
                    )
                    if len(block):
                        bucket_lines.append(
                            f"Inactive {label}: {int(len(block)):,} customer(s) holding "
                            f"{money(_safe_float(block['revenue'].sum()))} of historical revenue."
                        )
                return (
                    f"{int(len(inactive)):,} of {count:,} customers are potentially inactive "
                    f"({INACTIVE_DAYS}+ days without an order). Historical revenue from potentially "
                    f"inactive customers totals {money(lost_value)}.",
                    [
                        basis,
                        "This represents historical revenue associated with customers who have been "
                        f"inactive for {INACTIVE_DAYS}+ days. It is not a prediction of future revenue loss.",
                        f"Days are counted from the newest date in view ({end.strftime('%b %d, %Y')}).",
                        f"Largest quiet account: {_short(biggest.index[0], 40)} at {money(_safe_float(biggest['revenue'].iloc[0]))}, last seen {int(_safe_float(biggest['days_since'].iloc[0])):,} days ago.",
                        f"Retention rate is {retention:.1f}% ({count - int(len(inactive)):,} active customers).",
                    ]
                    + bucket_lines,
                    f"Run a win-back on {_short(biggest.index[0], 40)} first — the revenue is already proven.",
                    True,
                    "churn",
                )

            if _has(q, ("repeat", "retention", "loyal", "again", "twice")):
                return (
                    f"{repeat_rate:.1f}% of your customers bought more than once "
                    f"({int(len(repeat)):,} of {count:,}).",
                    [
                        basis,
                        f"Average of {_safe_float(grouped['rows'].mean()):.1f} rows per customer.",
                        f"Retention rate is {retention:.1f}% within {INACTIVE_DAYS} days of {end.strftime('%b %d, %Y')}.",
                        order_note,
                    ],
                    (
                        "A follow-up sequence after the first order is the cheapest way to lift this rate."
                        if repeat_rate < 40
                        else "Repeat buying is healthy — protect it with proactive account check-ins."
                    ),
                    True,
                    "customers",
                )

            if _has(q, ("how many", "number of", "count")):
                return (
                    f"You have {count:,} distinct customers in this selection.",
                    [
                        basis,
                        f"Revenue per customer averages {money(_safe_div(total, count))}.",
                        f"{int(len(repeat)):,} customers ordered more than once ({repeat_rate:.1f}%).",
                        f"{int(len(inactive)):,} customers are inactive for {INACTIVE_DAYS}+ days.",
                    ],
                    "Split effort between growing mid-tier accounts and re-activating the quiet ones.",
                    True,
                    "customers",
                )

            top_five = ranked.head(min(5, count))
            top_ten = ranked.head(min(10, count))
            five_share = (
                _safe_div(_safe_float(top_five["revenue"].sum()), total) * 100
            )
            ten_share = (
                _safe_div(_safe_float(top_ten["revenue"].sum()), total) * 100
            )
            level = (
                "High concentration"
                if leader_share >= 30 or five_share >= 60
                else (
                    "Moderate concentration"
                    if leader_share >= 15 or five_share >= 35
                    else "Low concentration"
                )
            )
            if _has(
                q,
                (
                    "concentration",
                    "concentrated",
                    "reliance",
                    "depend",
                    "top 5",
                    "top five",
                    "top 10",
                    "top ten",
                ),
            ):
                return (
                    f"Customer concentration is {level.lower()} — top 1 customer "
                    f"{leader_share:.1f}%, top {int(len(top_five))} {five_share:.1f}%, "
                    f"top {int(len(top_ten))} {ten_share:.1f}% of revenue.",
                    [
                        basis,
                        f"Top 1 ({leader}): {money(leader_value)} of {money(total)}.",
                        f"Top {int(len(top_five))}: {money(_safe_float(top_five['revenue'].sum()))} "
                        f"({five_share:.1f}%).",
                        f"Top {int(len(top_ten))}: {money(_safe_float(top_ten['revenue'].sum()))} "
                        f"({ten_share:.1f}%).",
                        f"{count:,} distinct customers appear in “{cust_col}”.",
                    ],
                    (
                        "Protect the largest accounts and grow the next tier to spread the risk."
                        if level != "Low concentration"
                        else "Revenue is well spread — keep the base broad as you grow."
                    ),
                    True,
                    "concentration",
                )
            return (
                f"{leader} is your top customer with {money(leader_value)} — "
                f"{leader_share:.1f}% of revenue in this selection.",
                [
                    basis,
                    f"{leader} appears on {int(_safe_float(ranked['rows'].iloc[0])):,} row(s), "
                    f"last ordering {pd.Timestamp(ranked['last_order'].iloc[0]).strftime('%b %d, %Y')}.",
                    f"Your top {int(len(top_five))} customers carry {five_share:.1f}% of revenue "
                    f"({money(_safe_float(top_five['revenue'].sum()))} of {money(total)}).",
                    f"Top {int(len(top_ten))} customers carry {ten_share:.1f}% — {level.lower()}.",
                    f"{count:,} distinct customers appear in “{cust_col}”.",
                ],
                (
                    f"{leader} alone carries {leader_share:.1f}% of revenue — build a retention plan for that account and grow the next tier to spread the risk."
                    if leader_share >= 25
                    else f"Keep {leader} close, and use the top five as the template for mid-tier growth."
                ),
                True,
                "customers",
            )

        # ---------------- products ----------------
        product_words = (
            "product",
            "category",
            "item",
            "sku",
            "sell best",
            "best seller",
            "bestseller",
            "service",
        )
        if _has(q, product_words):
            if not has_prod:
                return (
                    CANT_ANSWER,
                    [
                        "No product or category column is mapped, so revenue can't be grouped by product."
                    ],
                    "Map a product or category column on the upload page.",
                    False,
                    "products",
                )
            totals = _group(df, prod_col)
            if totals.empty:
                return (
                    CANT_ANSWER,
                    ["The mapped product column had no usable values."],
                    "Check the product column in your export and upload it again.",
                    False,
                    "products",
                )
            weakest = _has(
                q, ("worst", "weakest", "lowest", "least", "poorest")
            )
            index = -1 if weakest else 0
            name = _short(totals.index[index], 40)
            value = _safe_float(totals.iloc[index])
            share = _safe_div(value, total) * 100
            leader_name = _short(totals.index[0], 40)
            leader_share = _safe_div(_safe_float(totals.iloc[0]), total) * 100
            return (
                (
                    f"{name} is your weakest line at {money(value)} — {share:.1f}% of revenue."
                    if weakest
                    else f"{name} sells best with {money(value)} — {share:.1f}% of revenue."
                ),
                [
                    basis,
                    f"{int(totals.size):,} distinct value(s) in “{prod_col}”.",
                    f"Top line: {leader_name} at {money(_safe_float(totals.iloc[0]))} ({leader_share:.1f}%).",
                    f"Bottom line: {_short(totals.index[-1], 40)} at {money(_safe_float(totals.iloc[-1]))}.",
                ],
                (
                    f"Decide whether {name} is worth keeping, repricing or bundling with {leader_name}."
                    if weakest
                    else (
                        f"{leader_name} carries {leader_share:.1f}% of revenue — grow the next two lines so the mix is less dependent on it."
                        if leader_share >= 40
                        else f"Give {leader_name} more inventory and promotion weight while testing the mid-tier lines."
                    )
                ),
                True,
                "products",
            )

        # ---------------- region ----------------
        if _has(
            q,
            (
                "region",
                "country",
                "where",
                "location",
                "market",
                "city",
                "state",
            ),
        ):
            used = {
                cust_col,
                prod_col,
                order_col,
                _col(mapping, "date"),
                _col(mapping, "revenue"),
            }
            region_col = _find_region_column(df, {c for c in used if c})
            if not region_col:
                return (
                    CANT_ANSWER,
                    [
                        "No region, country, state or city column exists in the cleaned file."
                    ],
                    "Include a location column in your export to analyse revenue by region.",
                    False,
                    "region",
                )
            totals = _group(df, region_col)
            leader = _short(totals.index[0], 40)
            leader_value = _safe_float(totals.iloc[0])
            share = _safe_div(leader_value, total) * 100
            return (
                f"{leader} is your strongest area in “{region_col}” with {money(leader_value)} ({share:.1f}% of revenue).",
                [
                    basis,
                    f"{int(totals.size):,} distinct value(s) in “{region_col}”.",
                    f"Weakest: {_short(totals.index[-1], 40)} at {money(_safe_float(totals.iloc[-1]))}.",
                ],
                f"Compare what is working in {leader} against the weakest area before adding spend there.",
                True,
                "region",
            )

        # ---------------- growth / trend ----------------
        if _has(
            q,
            (
                "grow",
                "growth",
                "declin",
                "trend",
                "increase",
                "decrease",
                "up or down",
                "falling",
                "rising",
                "month over month",
                "mom",
            ),
        ):
            if len(values) < 2:
                return (
                    CANT_ANSWER,
                    [
                        f"All rows in view fall inside a single month ({labels[0] if labels else 'one period'}).",
                        "At least two months are needed to measure growth.",
                    ],
                    "Widen the date filter or upload a longer export to compare months.",
                    False,
                    "growth",
                )
            if month_complete or mtd_window == 0:
                latest, prior = values[-1], values[-2]
                headline = "Month-over-month"
                comparison = f"{labels[-1]} vs {labels[-2]} (complete months)"
                period_note = f"{labels[-1]} is a complete month in your file."
            else:
                latest, prior = mtd_current, mtd_previous
                headline = "Month-to-Date"
                comparison = (
                    f"{labels[-1]} days 1\u2013{mtd_window} vs "
                    f"{labels[-2]} days 1\u2013{mtd_window}"
                )
                period_note = (
                    f"{labels[-1]} is still in progress (data ends "
                    f"{end.strftime('%b %d, %Y')}), so I compare the first "
                    f"{mtd_window} day(s) of each month instead of a partial month "
                    "against a complete one."
                )
            change = (
                _safe_div(latest - prior, abs(prior)) * 100 if prior else 0.0
            )
            direction = (
                "grew"
                if change > 0
                else ("fell" if change < 0 else "held flat")
            )
            first_half = sum(values[: len(values) // 2])
            second_half = sum(values[len(values) // 2 :])
            half_change = (
                _safe_div(second_half - first_half, abs(first_half)) * 100
                if first_half
                else 0.0
            )
            large_note = (
                " This is a change of more than 30%, so verify data completeness "
                "before making business decisions."
                if abs(change) > 30
                else ""
            )
            return (
                f"{headline} revenue {direction} {abs(change):.1f}% — {money(latest)} against "
                f"{money(prior)} ({comparison}).{large_note}",
                [
                    basis,
                    period_note,
                    f"Compared window: {comparison}.",
                    f"Current: {money(latest)}. Previous: {money(prior)}.",
                    f"Second half of the period is {_pct(half_change)} versus the first half.",
                    f"{len(values)} month(s) of history are in view.",
                ],
                (
                    f"Find what changed in {labels[-1]} versus {labels[-2]} — start with the products and customers that moved most."
                    if change < 0
                    else f"Document what drove {labels[-1]} and repeat it; the gain is {money(latest - prior)}."
                ),
                True,
                "growth",
            )

        # ---------------- best / worst month ----------------
        if _has(
            q,
            (
                "best month",
                "strongest",
                "peak",
                "highest month",
                "worst month",
                "weakest month",
                "lowest month",
                "season",
                "busiest",
                "slow",
            ),
        ):
            if not values:
                return (
                    CANT_ANSWER,
                    ["No month could be summarised from the rows in view."],
                    "Check that the mapped date column contains readable dates.",
                    False,
                    "seasonality",
                )
            best = values.index(max(values))
            worst = values.index(min(values))
            average = sum(values) / len(values)
            weakest = _has(q, ("worst", "weakest", "lowest", "slow"))
            focus = worst if weakest else best
            return (
                (
                    f"{labels[focus]} was your weakest month at {money(values[focus])}."
                    if weakest
                    else f"{labels[focus]} was your strongest month at {money(values[focus])}."
                ),
                [
                    basis,
                    f"Monthly average is {money(average)} across {len(values)} month(s).",
                    f"Strongest: {labels[best]} at {money(values[best])}.",
                    f"Weakest: {labels[worst]} at {money(values[worst])}.",
                    f"{labels[focus]} carried {counts[focus]:,} row(s).",
                ],
                f"Plan campaigns and stock around this pattern — lift {labels[worst]} and protect {labels[best]}.",
                True,
                "seasonality",
            )

        # ---------------- average order value ----------------
        if _has(
            q,
            (
                "average order",
                "aov",
                "average sale",
                "average revenue",
                "basket",
                "per order",
            ),
        ):
            return (
                f"Average order value is {money(aov)}.",
                [
                    basis,
                    f"{money(total)} of revenue ÷ {orders:,} orders.",
                    order_note,
                    f"Largest single row is {money(_safe_float(df['_rev'].max()))}; smallest is {money(_safe_float(df['_rev'].min()))}.",
                ],
                "Bundling or a minimum-order incentive is the fastest lever on this number.",
                True,
                "aov",
            )

        # ---------------- orders ----------------
        if _has(q, ("order", "transaction", "invoice", "how many sales")):
            return (
                f"There are {orders:,} orders in this selection.",
                [
                    basis,
                    order_note,
                    f"Total revenue across them is {money(total)}.",
                    f"Average order value is {money(aov)}.",
                ],
                "Track order count and average order value together — one can hide a fall in the other.",
                True,
                "orders",
            )

        # ---------------- revenue / totals ----------------
        if _has(
            q,
            (
                "revenue",
                "sales",
                "total",
                "turnover",
                "how much",
                "income",
                "earned",
                "money",
            ),
        ):
            evidence = [
                basis,
                f"{orders:,} orders at an average of {money(aov)}.",
                order_note,
            ]
            if values:
                evidence.append(
                    f"Latest month in view, {labels[-1]}, contributed {money(values[-1])}."
                )
            if has_cust:
                cust_total = int(
                    df[cust_col]
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .nunique()
                )
                evidence.append(
                    f"{cust_total:,} distinct customers generated it, averaging {money(_safe_div(total, cust_total))} each."
                )
            return (
                f"Total revenue is {money(total)} across {period}.",
                evidence,
                (
                    f"Compare {labels[-1]} with {labels[-2]} to see whether this total is still trending up."
                    if len(values) > 1
                    else "Upload a longer history to see whether this total is trending up or down."
                ),
                True,
                "revenue",
            )

        # ---------------- fallback ----------------
        return (
            CANT_ANSWER,
            [
                "That question doesn't map to a figure I can calculate from your columns.",
                "I only answer from the mapped date, revenue, customer, product, order, cost and location columns.",
            ],
            "Try one of the suggested questions, or map more columns on the upload page for deeper answers.",
            False,
            "unknown",
        )
