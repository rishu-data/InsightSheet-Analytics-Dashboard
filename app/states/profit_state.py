import logging
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
    money,
)

INDIGO = "#4f46e5"
INDIGO_SOFT = "rgba(79, 70, 229, 0.12)"
BLUE = "#2563eb"
RED = "#ef4444"
GRID = "#eef2f7"

PROFIT_HINTS: list[str] = [
    "gross profit",
    "net profit",
    "total profit",
    "profit amount",
    "operating profit",
    "profit",
    "margin amount",
    "earnings",
    "margin",
]
_NOT_PROFIT = ("%", "percent", "rate", "ratio", "per unit", "/unit")

COST_HINTS: list[str] = [
    "total cost",
    "cost of goods",
    "cost of sales",
    "cogs",
    "total expense",
    "expenses",
    "expense",
    "cost",
    "spend",
]
_NOT_COST = ("per unit", "unit cost", "cost/unit", "per item", "%", "percent")

UNIT_COST_HINTS: list[str] = [
    "unit cost",
    "cost per unit",
    "cost/unit",
    "cost per item",
    "purchase price",
    "buy price",
    "wholesale price",
    "landed cost",
]

UNITS_HINTS: list[str] = [
    "units sold",
    "unit sold",
    "units ordered",
    "quantity sold",
    "quantity",
    "qty",
    "units",
    "volume",
]

MARGIN_PCT_HINTS: list[str] = [
    "profit margin",
    "gross margin",
    "net margin",
    "margin",
]


class ProfitRow(TypedDict):
    name: str
    revenue_display: str
    cost_display: str
    profit_display: str
    margin_display: str
    share_display: str
    tone: str


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[,$€£%\s]", "", regex=True),
        errors="coerce",
    )


def _norm(name: object) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def _filled_count(df: pd.DataFrame, col: str) -> int:
    text = df[col].astype(str).str.strip().str.lower()
    return int(
        (~text.isin(("", "nan", "none", "null", "n/a", "na", "-"))).sum()
    )


def _is_numeric_column(df: pd.DataFrame, col: str) -> bool:
    filled = _filled_count(df, col)
    if filled == 0:
        return False
    good = int(_numeric(df[col]).notna().sum())
    return good >= max(1, int(filled * 0.6))


def _pick(
    df: pd.DataFrame,
    columns: list[str],
    hints: list[str],
    exclude: tuple[str, ...],
    used: set[str],
) -> str:
    for hint in hints:
        for col in columns:
            if col in used:
                continue
            name = _norm(col)
            if any(bad in name for bad in exclude):
                continue
            if hint in name and _is_numeric_column(df, col):
                return col
    return ""


def _pick_margin_percent(
    df: pd.DataFrame, columns: list[str], used: set[str]
) -> tuple[str, pd.Series | None]:
    """A margin column only counts as a percentage when it looks like one."""
    for hint in MARGIN_PCT_HINTS:
        for col in columns:
            if col in used:
                continue
            name = _norm(col)
            if hint not in name:
                continue
            if not _is_numeric_column(df, col):
                continue
            values = _numeric(df[col]).dropna()
            if values.empty:
                continue
            named_percent = any(
                token in name
                for token in ("%", "percent", "rate", "ratio", "pct")
            )
            top = float(values.abs().max())
            if named_percent and top <= 100:
                return (col, values / 100 if top > 1 else values)
            if top <= 1:
                return (col, values)
    return ("", None)


class ProfitState(rx.State):
    available: bool = False
    blocked_reason: str = "Upload a spreadsheet with cost, profit or unit-cost data to unlock profit analysis."
    missing_hints: list[str] = []

    method_label: str = ""
    method_formula: str = ""
    cost_basis: str = ""
    rows_used: int = 0
    rows_skipped: int = 0

    total_profit: float = 0.0
    total_profit_display: str = "$0.00"
    total_revenue_display: str = "$0.00"
    total_cost_display: str = "$0.00"
    cost_share: float = 0.0
    profit_margin: float = 0.0
    profit_per_order_display: str = "$0.00"
    order_caption: str = "Rows with revenue and profit"
    profit_orders: int = 0
    is_profitable: bool = True

    loss_rows: int = 0
    loss_amount_display: str = "$0.00"

    has_trend: bool = False
    profit_trend_figure: go.Figure = _blank_figure("No profit trend yet")
    best_month: str = ""
    best_month_display: str = ""
    worst_month: str = ""
    worst_month_display: str = ""
    months_covered: int = 0
    profit_growth: float = 0.0
    growth_direction: str = "flat"
    growth_caption: str = "Not enough monthly history yet"

    has_product_profit: bool = False
    product_profit_figure: go.Figure = _blank_figure("No product column mapped")
    has_customer_profit: bool = False
    customer_profit_figure: go.Figure = _blank_figure(
        "No customer column mapped"
    )

    has_margin_table: bool = False
    margin_table_label: str = "Item"
    margin_table: list[ProfitRow] = []
    best_margin_name: str = ""
    best_margin_display: str = ""
    worst_margin_name: str = ""
    worst_margin_display: str = ""
    loss_items: int = 0

    summary_points: list[str] = []

    @rx.var
    def total_profit_signed(self) -> str:
        sign = "-" if self.total_profit < 0 else ""
        return f"{sign}{money(abs(self.total_profit))}"

    @rx.var
    def margin_display(self) -> str:
        return f"{self.profit_margin:.1f}%"

    @rx.var
    def growth_display(self) -> str:
        sign = "+" if self.profit_growth > 0 else ""
        return f"{sign}{self.profit_growth:.1f}%"

    @rx.event
    async def compute_profit(self):
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        if not records:
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll look for cost or profit data.",
                [
                    "A revenue or sales amount column",
                    "A cost column, a profit column, or units sold with a unit cost",
                ],
            )
            return
        try:
            self._build(records, mapping)
        except Exception as e:
            logging.exception(f"Error computing profit metrics: {e}")
            self._unavailable(
                "We couldn't calculate profit from those columns. Check the cost or profit column in your file.",
                ["Numeric cost, profit or unit-cost values"],
            )

    def _unavailable(self, reason: str, hints: list[str]) -> None:
        self.available = False
        self.blocked_reason = reason
        self.missing_hints = hints
        self.method_label = ""
        self.method_formula = ""
        self.cost_basis = ""
        self.rows_used = 0
        self.rows_skipped = 0
        self.total_profit = 0.0
        self.total_profit_display = "$0.00"
        self.total_revenue_display = "$0.00"
        self.total_cost_display = "$0.00"
        self.cost_share = 0.0
        self.profit_margin = 0.0
        self.profit_per_order_display = "$0.00"
        self.order_caption = "Rows with revenue and profit"
        self.profit_orders = 0
        self.is_profitable = True
        self.loss_rows = 0
        self.loss_amount_display = "$0.00"
        self.has_trend = False
        self.profit_trend_figure = _blank_figure("No profit trend yet")
        self.best_month = ""
        self.best_month_display = ""
        self.worst_month = ""
        self.worst_month_display = ""
        self.months_covered = 0
        self.profit_growth = 0.0
        self.growth_direction = "flat"
        self.growth_caption = "Not enough monthly history yet"
        self.has_product_profit = False
        self.product_profit_figure = _blank_figure("No product column mapped")
        self.has_customer_profit = False
        self.customer_profit_figure = _blank_figure("No customer column mapped")
        self.has_margin_table = False
        self.margin_table_label = "Item"
        self.margin_table = []
        self.best_margin_name = ""
        self.best_margin_display = ""
        self.worst_margin_name = ""
        self.worst_margin_display = ""
        self.loss_items = 0
        self.summary_points = []

    def _build(
        self, records: list[dict[str, str]], mapping: dict[str, str]
    ) -> None:
        if not records:
            self._unavailable(
                "Upload a spreadsheet on the upload page and we'll look for cost or profit data.",
                [
                    "A revenue or sales amount column",
                    "A cost column, a profit column, or units sold with a unit cost",
                ],
            )
            return
        rev_col = _col(mapping, "revenue")
        date_col = _col(mapping, "date")
        prod_col = _col(mapping, "product")
        cust_col = _col(mapping, "customer")
        order_col = _col(mapping, "order_id")

        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._unavailable(
                "There are no cleaned rows to calculate profit from yet.",
                ["At least one row with a revenue value and a cost or profit"],
            )
            return
        columns = [str(c) for c in df.columns]
        if not rev_col or rev_col not in df.columns:
            self._unavailable(
                "Profit analysis needs a revenue column. Map one on the upload page first.",
                ["A revenue or sales amount column"],
            )
            return

        df["_rev"] = _numeric(df[rev_col])
        used = {rev_col}
        profit_col = _pick(df, columns, PROFIT_HINTS, _NOT_PROFIT, used)
        cost_col = _pick(df, columns, COST_HINTS, _NOT_COST, used)
        unit_cost_col = _pick(df, columns, UNIT_COST_HINTS, ("%",), used)
        units_col = _pick(df, columns, UNITS_HINTS, ("%", "price"), used)
        margin_col, margin_fraction = _pick_margin_percent(df, columns, used)

        if profit_col:
            df["_profit"] = _numeric(df[profit_col])
            df["_cost"] = df["_rev"] - df["_profit"]
            self.method_label = f"Read straight from your “{profit_col}” column"
            self.method_formula = f"Profit = {profit_col}"
            self.cost_basis = f"Cost shown below is {rev_col} − {profit_col}"
        elif cost_col:
            df["_cost"] = _numeric(df[cost_col])
            df["_profit"] = df["_rev"] - df["_cost"]
            self.method_label = (
                f"Calculated from your “{rev_col}” and “{cost_col}” columns"
            )
            self.method_formula = f"Profit = {rev_col} − {cost_col}"
            self.cost_basis = f"Cost is the “{cost_col}” column as-is"
        elif units_col and unit_cost_col:
            df["_cost"] = _numeric(df[units_col]) * _numeric(df[unit_cost_col])
            df["_profit"] = df["_rev"] - df["_cost"]
            self.method_label = f"Calculated from “{rev_col}” minus “{units_col}” × “{unit_cost_col}”"
            self.method_formula = (
                f"Profit = {rev_col} − ({units_col} × {unit_cost_col})"
            )
            self.cost_basis = f"Cost is {units_col} × {unit_cost_col}"
        elif margin_col and margin_fraction is not None:
            fraction = pd.to_numeric(_numeric(df[margin_col]), errors="coerce")
            top_value = _safe_float(fraction.abs().max())
            scale = 100.0 if top_value > 1 else 1.0
            df["_profit"] = df["_rev"] * (fraction / scale)
            df["_cost"] = df["_rev"] - df["_profit"]
            self.method_label = f"Calculated from “{rev_col}” and your “{margin_col}” percentage"
            self.method_formula = f"Profit = {rev_col} × {margin_col}"
            self.cost_basis = f"Cost shown below is {rev_col} − profit"
        else:
            self._unavailable(
                "Your file doesn't contain enough information to work out profit. "
                "We never estimate margins, so nothing is shown until real cost data is present.",
                [
                    "A profit column (for example “Gross Profit”), or",
                    "A cost column such as “Cost”, “COGS” or “Total Cost”, or",
                    "Units sold together with a unit cost column, or",
                    "A profit margin percentage column",
                ],
            )
            return

        total_rows = int(len(df))
        df = df.dropna(subset=["_rev", "_profit"])
        if df.empty:
            self._unavailable(
                "None of the rows had both a numeric revenue value and a usable cost or profit value.",
                ["Numeric revenue and cost/profit values on the same row"],
            )
            return

        self.rows_used = int(len(df))
        self.rows_skipped = max(0, total_rows - self.rows_used)

        revenue = _safe_float(df["_rev"].sum())
        profit = _safe_float(df["_profit"].sum())
        cost = _safe_float(df["_cost"].fillna(0).sum())
        self.total_profit = round(profit, 2)
        self.total_profit_display = money(profit)
        self.total_revenue_display = money(revenue)
        self.total_cost_display = money(cost)
        self.cost_share = round(_safe_div(cost, revenue) * 100, 1)
        self.profit_margin = round(_safe_div(profit, revenue) * 100, 1)
        self.is_profitable = profit >= 0

        orders = self.rows_used
        if order_col and order_col in df.columns:
            keys = df[order_col].astype(str).str.strip()
            distinct = int(keys[keys != ""].nunique())
            orders = distinct or orders
            self.order_caption = f"Distinct values in “{order_col}”"
        else:
            self.order_caption = "Rows with revenue and profit"
        self.profit_orders = orders
        self.profit_per_order_display = money(_safe_div(profit, orders))

        losses = df[df["_profit"] < 0]
        self.loss_rows = int(len(losses))
        self.loss_amount_display = money(
            abs(_safe_float(losses["_profit"].sum()))
        )

        self._build_trend(df, date_col)
        top_product = (
            self._build_rank_figure(df, prod_col, profit, "product")
            if prod_col and prod_col in df.columns
            else None
        )
        top_customer = (
            self._build_rank_figure(df, cust_col, profit, "customer")
            if cust_col and cust_col in df.columns
            else None
        )
        self._build_margin_table(df, prod_col, cust_col, profit)
        self._build_summary(top_product, top_customer)
        self.available = True
        self.blocked_reason = ""
        self.missing_hints = []

    def _build_trend(self, df: pd.DataFrame, date_col: str) -> None:
        if not date_col or date_col not in df.columns:
            self.has_trend = False
            self.profit_trend_figure = _blank_figure(
                "Map a date column to see profit over time"
            )
            self.growth_caption = "No date column mapped"
            return
        work = df.assign(_date=_to_datetime(df[date_col]))
        work = work.dropna(subset=["_date"])
        if work.empty:
            self.has_trend = False
            self.profit_trend_figure = _blank_figure(
                "No readable dates in the mapped date column"
            )
            self.growth_caption = "No readable dates"
            return

        monthly = (
            work.set_index("_date")[["_rev", "_profit"]].resample("MS").sum()
        )
        labels = [pd.Timestamp(i).strftime("%b %Y") for i in monthly.index]
        profits = [_safe_float(v) for v in monthly["_profit"].to_numpy()]
        revenues = [_safe_float(v) for v in monthly["_rev"].to_numpy()]
        margins = [
            round(_safe_div(p, r) * 100, 1) for p, r in zip(profits, revenues)
        ]
        self.months_covered = len(labels)
        if not profits:
            self.has_trend = False
            self.profit_trend_figure = _blank_figure(
                "No monthly profit to chart yet"
            )
            self.growth_caption = "Not enough monthly history yet"
            return

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=labels,
                y=profits,
                name="Profit",
                marker_color=[INDIGO if p >= 0 else RED for p in profits],
                hovertemplate="%{x}<br>Profit $%{y:,.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=margins,
                name="Margin %",
                yaxis="y2",
                mode="lines+markers",
                line={"color": BLUE, "width": 2.5},
                marker={"size": 6, "color": BLUE},
                hovertemplate="%{x}<br>Margin %{y:.1f}%<extra></extra>",
            )
        )
        fig.update_layout(
            height=340,
            autosize=True,
            margin={"l": 55, "r": 55, "t": 20, "b": 45},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            showlegend=False,
            bargap=0.35,
            hovermode="x unified",
            xaxis={"showgrid": False, "linecolor": GRID},
            yaxis={
                "title": "Profit",
                "gridcolor": GRID,
                "zerolinecolor": GRID,
                "tickprefix": "$",
            },
            yaxis2={
                "title": "Margin %",
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
                "ticksuffix": "%",
            },
        )
        self.profit_trend_figure = fig
        self.has_trend = True

        best_idx = profits.index(max(profits))
        worst_idx = profits.index(min(profits))
        self.best_month = labels[best_idx]
        self.best_month_display = money(profits[best_idx])
        self.worst_month = labels[worst_idx]
        self.worst_month_display = money(profits[worst_idx])

        if len(profits) > 1 and profits[-2] != 0:
            change = (
                _safe_div(profits[-1] - profits[-2], abs(profits[-2])) * 100
            )
            self.profit_growth = round(change, 1)
            self.growth_direction = (
                "up" if change > 0 else ("down" if change < 0 else "flat")
            )
            self.growth_caption = f"{labels[-1]} vs {labels[-2]}"
        else:
            self.profit_growth = 0.0
            self.growth_direction = "flat"
            self.growth_caption = (
                "Only one month of data"
                if len(profits) == 1
                else "Not enough monthly history yet"
            )

    def _build_rank_figure(
        self, df: pd.DataFrame, column: str, total_profit: float, kind: str
    ) -> tuple[str, float, float] | None:
        grouped = (
            df.assign(
                _key=df[column].astype(str).str.strip().replace("", "(blank)")
            )
            .groupby("_key")[["_rev", "_profit"]]
            .sum()
            .sort_values("_profit", ascending=False)
        )
        if grouped.empty:
            return None
        top = grouped.head(8)
        names = [_short(n) for n in top.index]
        profits = [_safe_float(v) for v in top["_profit"].to_numpy()]
        revenues = [_safe_float(v) for v in top["_rev"].to_numpy()]
        if not profits:
            return None
        labels = [
            f"{money(p)} · {_safe_div(p, r) * 100:.1f}% margin"
            for p, r in zip(profits, revenues)
        ]
        fig = go.Figure(
            go.Bar(
                x=profits,
                y=names,
                orientation="h",
                text=labels,
                textposition="outside",
                cliponaxis=False,
                marker_color=[INDIGO if p >= 0 else RED for p in profits],
                textfont={"size": 11, "color": "#475569"},
                hovertemplate="%{y}<br>Profit $%{x:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=340,
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
            xaxis={
                "gridcolor": GRID,
                "tickprefix": "$",
                "zerolinecolor": GRID,
            },
            yaxis={"autorange": "reversed", "showgrid": False},
        )
        if kind == "product":
            self.product_profit_figure = fig
            self.has_product_profit = True
        else:
            self.customer_profit_figure = fig
            self.has_customer_profit = True
        leader_profit = profits[0]
        leader_revenue = revenues[0]
        share = _safe_div(leader_profit, total_profit) * 100
        margin = _safe_div(leader_profit, leader_revenue) * 100
        return (_short(top.index[0], 40), share, margin)

    def _build_margin_table(
        self,
        df: pd.DataFrame,
        prod_col: str,
        cust_col: str,
        total_profit: float,
    ) -> None:
        column = ""
        label = "Item"
        if prod_col and prod_col in df.columns:
            column = prod_col
            label = "Product / Category"
        elif cust_col and cust_col in df.columns:
            column = cust_col
            label = "Customer"
        if not column:
            self.has_margin_table = False
            self.margin_table = []
            self.best_margin_name = ""
            self.best_margin_display = ""
            self.worst_margin_name = ""
            self.worst_margin_display = ""
            self.loss_items = 0
            return

        grouped = (
            df.assign(
                _key=df[column].astype(str).str.strip().replace("", "(blank)")
            )
            .groupby("_key")[["_rev", "_profit"]]
            .sum()
        )
        if grouped.empty:
            self.has_margin_table = False
            self.margin_table = []
            self.best_margin_name = ""
            self.best_margin_display = ""
            self.worst_margin_name = ""
            self.worst_margin_display = ""
            self.loss_items = 0
            return
        grouped["_cost"] = grouped["_rev"] - grouped["_profit"]
        grouped["_margin"] = [
            _safe_div(_safe_float(p), _safe_float(r)) * 100
            for p, r in zip(grouped["_profit"], grouped["_rev"])
        ]
        grouped = grouped.sort_values("_margin", ascending=False)

        rows: list[ProfitRow] = []
        for name, row in grouped.iterrows():
            margin = _safe_float(row["_margin"])
            profit = _safe_float(row["_profit"])
            share = _safe_div(profit, total_profit) * 100
            tone = "loss" if profit < 0 else ("low" if margin < 15 else "good")
            rows.append(
                ProfitRow(
                    name=_short(name, 32),
                    revenue_display=money(_safe_float(row["_rev"])),
                    cost_display=money(_safe_float(row["_cost"])),
                    profit_display=money(profit),
                    margin_display=f"{margin:.1f}%",
                    share_display=f"{share:.1f}%",
                    tone=tone,
                )
            )

        self.margin_table_label = label
        self.margin_table = rows[:20]
        self.has_margin_table = len(rows) > 0
        self.best_margin_name = rows[0]["name"] if rows else ""
        self.best_margin_display = rows[0]["margin_display"] if rows else ""
        self.worst_margin_name = rows[-1]["name"] if rows else ""
        self.worst_margin_display = rows[-1]["margin_display"] if rows else ""
        self.loss_items = int((grouped["_profit"] < 0).sum())

    def _build_summary(
        self,
        top_product: tuple[str, float, float] | None,
        top_customer: tuple[str, float, float] | None,
    ) -> None:
        points: list[str] = [
            f"{self.method_label} — {self.method_formula}.",
            f"Profit totals {self.total_profit_display} on {self.total_revenue_display} of revenue, "
            f"an overall margin of {self.profit_margin:.1f}%.",
            f"Cost of sales totals {self.total_cost_display}, which is {self.cost_share:.1f}% of revenue.",
            f"That works out to {self.profit_per_order_display} of profit per order across "
            f"{self.profit_orders:,} orders.",
        ]
        if self.rows_skipped:
            points.append(
                f"{self.rows_skipped:,} row(s) were left out because they had no usable revenue or cost value."
            )
        if self.has_trend and self.best_month:
            points.append(
                f"{self.best_month} was the most profitable month at {self.best_month_display}; "
                f"{self.worst_month} was the weakest at {self.worst_month_display}."
            )
        if self.has_trend and self.growth_direction != "flat":
            verb = "rose" if self.growth_direction == "up" else "fell"
            points.append(
                f"Profit {verb} {abs(self.profit_growth):.1f}% in the latest month ({self.growth_caption})."
            )
        if top_product:
            points.append(
                f"{top_product[0]} contributes the most profit — {top_product[1]:.1f}% of total profit "
                f"at a {top_product[2]:.1f}% margin."
            )
        if top_customer:
            points.append(
                f"{top_customer[0]} is the most profitable customer, worth {top_customer[1]:.1f}% of total profit."
            )
        if self.has_margin_table and self.best_margin_name:
            points.append(
                f"Margins range from {self.best_margin_display} ({self.best_margin_name}) down to "
                f"{self.worst_margin_display} ({self.worst_margin_name})."
            )
        if self.loss_rows:
            points.append(
                f"{self.loss_rows:,} row(s) sold below cost, losing {self.loss_amount_display} in total."
            )
        else:
            points.append("Every row in your file sold at or above cost.")
        self.summary_points = points
