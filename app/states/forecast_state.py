"""Revenue forecasting from the uploaded, cleaned and filtered rows only.

The forecast is a plain least-squares trend fitted to *complete* monthly
revenue totals calculated from your own data, with a prediction interval
derived from the model's residuals. Nothing is invented: when there aren't
enough complete months to fit and validate a trend we refuse to forecast.
"""

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
    _to_datetime,
    _to_number,
    money,
)

MIN_MONTHS = 4
HORIZONS: list[int] = [3, 6, 12]
INSUFFICIENT = "Not enough historical data to generate a reliable forecast."

BLUE = "#2563eb"
INDIGO = "#4f46e5"
BAND = "rgba(79, 70, 229, 0.14)"
GRID = "#eef2f7"


class ForecastRow(TypedDict):
    month: str
    step: int
    value: float
    value_display: str
    low_display: str
    high_display: str
    range_display: str
    change_display: str
    direction: str


class HistoryRow(TypedDict):
    month: str
    value: float
    value_display: str


def _fit(values: list[float]) -> tuple[float, float, float, float]:
    """Least-squares fit over month index. Returns slope, intercept, r2, se."""
    n = len(values)
    xs = list(range(n))
    x_bar = sum(xs) / n
    y_bar = sum(values) / n
    sxx = sum((x - x_bar) ** 2 for x in xs)
    sxy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, values))
    slope = _safe_div(sxy, sxx)
    intercept = y_bar - slope * x_bar
    fitted = [intercept + slope * x for x in xs]
    ss_res = sum((y - f) ** 2 for y, f in zip(values, fitted))
    ss_tot = sum((y - y_bar) ** 2 for y in values)
    r2 = 1.0 - _safe_div(ss_res, ss_tot) if ss_tot > 0 else 0.0
    se = math.sqrt(_safe_div(ss_res, max(1, n - 2))) if n > 2 else 0.0
    return (slope, intercept, max(0.0, min(1.0, _safe_float(r2))), se)


def _margin(step_x: float, n: int, se: float) -> float:
    """95% prediction margin for a future month index."""
    if se <= 0 or n < 3:
        return 0.0
    xs = list(range(n))
    x_bar = sum(xs) / n
    sxx = sum((x - x_bar) ** 2 for x in xs)
    leverage = 1.0 + _safe_div(1.0, n) + _safe_div((step_x - x_bar) ** 2, sxx)
    return _safe_float(1.96 * se * math.sqrt(max(0.0, leverage)))


def _signed_pct(value: float) -> str:
    return f"{'+' if value > 0 else ''}{value:.1f}%"


class ForecastState(rx.State):
    """Monthly revenue forecast for the rows currently in view."""

    horizon: int = 3
    available: bool = False
    blocked_reason: str = INSUFFICIENT
    missing_hints: list[str] = []
    is_computing: bool = False

    # history basis
    months_used: int = 0
    history_start: str = ""
    history_end: str = ""
    history_total_display: str = "$0.00"
    average_month_display: str = "$0.00"
    last_month_label: str = ""
    last_month_display: str = "$0.00"
    partial_month_note: str = ""
    rows_used: int = 0
    filters_applied: int = 0

    # forecast output
    forecast_rows: list[ForecastRow] = []
    history_rows: list[HistoryRow] = []
    figure: go.Figure = _blank_figure("No forecast yet")

    next_month_label: str = ""
    next_month_display: str = "$0.00"
    next_month_range: str = ""
    next_month_change: float = 0.0
    next_month_direction: str = "flat"

    three_month_display: str = "$0.00"
    three_month_label: str = ""
    three_month_change: float = 0.0
    three_month_direction: str = "flat"
    three_month_basis: str = ""

    horizon_total_display: str = "$0.00"
    horizon_range: str = ""

    trend_direction: str = "flat"
    trend_label: str = "Flat"
    trend_per_month_display: str = "$0.00"
    trend_detail: str = ""

    confidence_label: str = "Low"
    confidence_tone: str = "warn"
    confidence_detail: str = ""
    fit_quality: float = 0.0
    band_available: bool = False

    method_note: str = ""
    summary_points: list[str] = []

    @rx.var
    def next_month_change_display(self) -> str:
        return _signed_pct(self.next_month_change)

    @rx.var
    def three_month_change_display(self) -> str:
        return _signed_pct(self.three_month_change)

    @rx.var
    def fit_display(self) -> str:
        return f"{self.fit_quality * 100:.0f}%"

    @rx.var
    def horizon_label(self) -> str:
        return f"Next {self.horizon} months"

    @rx.event
    def select_horizon(self, months: int):
        try:
            value = int(months)
        except (TypeError, ValueError):
            value = 3
        self.horizon = value if value in HORIZONS else 3
        return ForecastState.compute_forecast

    @rx.event
    async def compute_forecast(self):
        from app.states.filter_state import FilterState
        from app.states.upload_state import UploadState

        self.is_computing = True
        yield
        try:
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
                    INSUFFICIENT,
                    [
                        "Upload a sales export on the upload page",
                        "A date column and a revenue column mapped",
                        f"At least {MIN_MONTHS} complete months of history",
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
                    INSUFFICIENT,
                    missing
                    + [f"At least {MIN_MONTHS} complete months of history"],
                )
                return
            self._build(records, mapping, selections, dim_columns, start, end)
        except Exception as e:
            logging.exception(f"Error computing revenue forecast: {e}")
            self._unavailable(
                INSUFFICIENT,
                [
                    "Readable dates and numeric revenue values on the same row",
                    f"At least {MIN_MONTHS} complete months of history",
                ],
            )
        finally:
            self.is_computing = False

    def _unavailable(self, reason: str, hints: list[str]) -> None:
        self.available = False
        self.blocked_reason = reason
        self.missing_hints = hints
        self.months_used = 0
        self.history_start = ""
        self.history_end = ""
        self.history_total_display = "$0.00"
        self.average_month_display = "$0.00"
        self.last_month_label = ""
        self.last_month_display = "$0.00"
        self.partial_month_note = ""
        self.rows_used = 0
        self.filters_applied = 0
        self.forecast_rows = []
        self.history_rows = []
        self.figure = _blank_figure("No forecast yet")
        self.next_month_label = ""
        self.next_month_display = "$0.00"
        self.next_month_range = ""
        self.next_month_change = 0.0
        self.next_month_direction = "flat"
        self.three_month_display = "$0.00"
        self.three_month_label = ""
        self.three_month_change = 0.0
        self.three_month_direction = "flat"
        self.three_month_basis = ""
        self.horizon_total_display = "$0.00"
        self.horizon_range = ""
        self.trend_direction = "flat"
        self.trend_label = "Flat"
        self.trend_per_month_display = "$0.00"
        self.trend_detail = ""
        self.confidence_label = "Low"
        self.confidence_tone = "warn"
        self.confidence_detail = ""
        self.fit_quality = 0.0
        self.band_available = False
        self.method_note = ""
        self.summary_points = []

    # ------------------------------------------------------------------

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
        date_col = _col(mapping, "date")
        rev_col = _col(mapping, "revenue")

        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._unavailable(
                INSUFFICIENT,
                ["At least one cleaned row with a date and an amount"],
            )
            return
        if date_col not in df.columns or rev_col not in df.columns:
            self._unavailable(
                INSUFFICIENT,
                [
                    "Date and revenue columns that still exist in the cleaned file"
                ],
            )
            return

        df["_date"] = _to_datetime(df[date_col])
        df["_rev"] = _to_number(df[rev_col])
        df = df.dropna(subset=["_date", "_rev"])
        if df.empty:
            self._unavailable(
                INSUFFICIENT,
                ["Readable dates and numeric revenue values on the same row"],
            )
            return

        applied = 0
        start_stamp = (
            pd.to_datetime(str(start or "").strip(), errors="coerce")
            if start
            else None
        )
        end_stamp = (
            pd.to_datetime(str(end or "").strip(), errors="coerce")
            if end
            else None
        )
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
                INSUFFICIENT,
                [
                    "Rows that match the filters currently applied — widen the date range or clear a filter"
                ],
            )
            return

        self.filters_applied = applied
        monthly = df.set_index("_date")["_rev"].resample("MS").sum()
        stamps = [pd.Timestamp(i) for i in monthly.index]
        values = [_safe_float(v) for v in monthly.to_numpy()]

        # Drop a trailing partial month so the trend isn't fitted on half data.
        last_date = df["_date"].max()
        self.partial_month_note = ""
        if stamps:
            month_end = (
                stamps[-1] + pd.offsets.MonthEnd(0)
            ).normalize()  # last day of final month
            if last_date.normalize() < month_end and len(stamps) > 1:
                self.partial_month_note = (
                    f"{stamps[-1].strftime('%b %Y')} is still incomplete "
                    f"(data ends {last_date.strftime('%b %d, %Y')}), so it was excluded from the fit."
                )
                stamps = stamps[:-1]
                values = values[:-1]

        if len(values) < MIN_MONTHS:
            self._unavailable(
                INSUFFICIENT,
                [
                    f"At least {MIN_MONTHS} complete months of revenue — this selection has "
                    f"{len(values)}",
                    "A wider date range, or a longer export, gives a trend to fit",
                ],
            )
            return

        self.rows_used = int(len(df))
        self.months_used = len(values)
        self.history_start = stamps[0].strftime("%b %Y")
        self.history_end = stamps[-1].strftime("%b %Y")
        history_total = sum(values)
        average = history_total / len(values)
        self.history_total_display = money(history_total)
        self.average_month_display = money(average)
        self.last_month_label = stamps[-1].strftime("%b %Y")
        self.last_month_display = money(values[-1])
        self.history_rows = [
            HistoryRow(
                month=stamp.strftime("%b %Y"),
                value=round(value, 2),
                value_display=money(value),
            )
            for stamp, value in zip(stamps, values)
        ]

        slope, intercept, r2, se = _fit(values)
        n = len(values)
        steps = max(self.horizon, 3)
        rows: list[ForecastRow] = []
        previous = values[-1]
        for step in range(1, steps + 1):
            x = n - 1 + step
            point = max(0.0, intercept + slope * x)
            margin = _margin(float(x), n, se)
            low = max(0.0, point - margin)
            high = point + margin
            change = _safe_div(point - previous, abs(previous)) * 100
            direction = (
                "up" if change > 0.5 else ("down" if change < -0.5 else "flat")
            )
            stamp = stamps[-1] + pd.DateOffset(months=step)
            rows.append(
                ForecastRow(
                    month=pd.Timestamp(stamp).strftime("%b %Y"),
                    step=step,
                    value=round(point, 2),
                    value_display=money(point),
                    low_display=money(low),
                    high_display=money(high),
                    range_display=(
                        f"{money(low)} – {money(high)}"
                        if margin > 0
                        else "Range unavailable"
                    ),
                    change_display=_signed_pct(change),
                    direction=direction,
                )
            )
            previous = point

        visible = rows[: self.horizon]
        self.forecast_rows = visible
        self.band_available = se > 0

        first = rows[0]
        self.next_month_label = first["month"]
        self.next_month_display = first["value_display"]
        self.next_month_range = first["range_display"]
        self.next_month_change = round(
            _safe_div(first["value"] - values[-1], abs(values[-1])) * 100, 1
        )
        self.next_month_direction = (
            "up"
            if self.next_month_change > 0.5
            else ("down" if self.next_month_change < -0.5 else "flat")
        )

        three = rows[:3]
        three_total = sum(row["value"] for row in three)
        self.three_month_display = money(three_total)
        self.three_month_label = f"{three[0]['month']} – {three[-1]['month']}"
        recent_three = values[-3:]
        recent_total = sum(recent_three)
        self.three_month_change = round(
            _safe_div(three_total - recent_total, abs(recent_total)) * 100, 1
        )
        self.three_month_direction = (
            "up"
            if self.three_month_change > 0.5
            else ("down" if self.three_month_change < -0.5 else "flat")
        )
        self.three_month_basis = (
            f"Against {money(recent_total)} in the last 3 complete months "
            f"({stamps[-3].strftime('%b %Y')} – {stamps[-1].strftime('%b %Y')})"
        )

        horizon_total = sum(row["value"] for row in visible)
        self.horizon_total_display = money(horizon_total)
        low_total = sum(
            max(0.0, row["value"] - _margin(float(n - 1 + row["step"]), n, se))
            for row in visible
        )
        high_total = sum(
            row["value"] + _margin(float(n - 1 + row["step"]), n, se)
            for row in visible
        )
        self.horizon_range = (
            f"{money(low_total)} – {money(high_total)}"
            if se > 0
            else "Range unavailable"
        )

        self.trend_per_month_display = money(abs(slope))
        threshold = abs(average) * 0.01
        if slope > threshold:
            self.trend_direction = "up"
            self.trend_label = "Rising"
        elif slope < -threshold:
            self.trend_direction = "down"
            self.trend_label = "Declining"
        else:
            self.trend_direction = "flat"
            self.trend_label = "Flat"
        self.trend_detail = (
            f"The fitted trend moves {'up' if slope >= 0 else 'down'} "
            f"{money(abs(slope))} per month across {n} complete month(s)."
        )

        self.fit_quality = round(r2, 3)
        spread = _safe_div(se, average)
        if n >= 8 and r2 >= 0.6 and spread <= 0.2:
            self.confidence_label = "High"
            self.confidence_tone = "good"
        elif n >= 6 and (r2 >= 0.35 or spread <= 0.35):
            self.confidence_label = "Moderate"
            self.confidence_tone = "info"
        else:
            self.confidence_label = "Low"
            self.confidence_tone = "warn"
        self.confidence_detail = (
            f"The trend explains {r2 * 100:.0f}% of month-to-month movement, with a typical "
            f"miss of {money(se)} per month ({spread * 100:.0f}% of the {self.average_month_display} average). "
            f"Based on {n} complete month(s) — the more history, the tighter the range."
            if se > 0
            else f"Only {n} complete month(s) are available, so no uncertainty range can be measured."
        )
        self.method_note = (
            "Least-squares linear trend fitted to complete monthly revenue totals from your own rows, "
            "with a 95% prediction interval taken from the model's residuals."
        )
        self._build_figure(stamps, values, visible, se, n)
        self._build_summary()
        self.available = True
        self.blocked_reason = ""
        self.missing_hints = []

    def _build_figure(
        self,
        stamps: list[pd.Timestamp],
        values: list[float],
        rows: list[ForecastRow],
        se: float,
        n: int,
    ) -> None:
        hist_labels = [s.strftime("%b %Y") for s in stamps]
        fc_labels = [row["month"] for row in rows]
        fc_values = [row["value"] for row in rows]
        lows = [
            max(0.0, row["value"] - _margin(float(n - 1 + row["step"]), n, se))
            for row in rows
        ]
        highs = [
            row["value"] + _margin(float(n - 1 + row["step"]), n, se)
            for row in rows
        ]

        # Bridge the last actual month into the forecast for a continuous line.
        bridge_labels = [hist_labels[-1]] + fc_labels
        bridge_values = [values[-1]] + fc_values
        bridge_low = [values[-1]] + lows
        bridge_high = [values[-1]] + highs

        fig = go.Figure()
        if se > 0:
            fig.add_trace(
                go.Scatter(
                    x=bridge_labels,
                    y=bridge_high,
                    name="Upper estimate",
                    mode="lines",
                    line={"width": 0, "color": INDIGO},
                    hovertemplate="%{x}<br>Upper estimate $%{y:,.2f}<extra></extra>",
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=bridge_labels,
                    y=bridge_low,
                    name="Lower estimate",
                    mode="lines",
                    line={"width": 0, "color": INDIGO},
                    fill="tonexty",
                    fillcolor=BAND,
                    hovertemplate="%{x}<br>Lower estimate $%{y:,.2f}<extra></extra>",
                    showlegend=False,
                )
            )
        fig.add_trace(
            go.Scatter(
                x=hist_labels,
                y=values,
                name="Actual revenue",
                mode="lines+markers",
                line={"color": BLUE, "width": 2.5},
                marker={"size": 6, "color": BLUE},
                hovertemplate="%{x}<br>Actual $%{y:,.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=bridge_labels,
                y=bridge_values,
                name="Forecast (estimate)",
                mode="lines+markers",
                line={"color": INDIGO, "width": 2.5, "dash": "dash"},
                marker={"size": 7, "color": INDIGO, "symbol": "diamond"},
                hovertemplate="%{x}<br>Forecast $%{y:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=360,
            autosize=True,
            margin={"l": 55, "r": 25, "t": 20, "b": 55},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#ffffff",
            font={
                "family": "Inter, sans-serif",
                "size": 12,
                "color": "#64748b",
            },
            hovermode="x unified",
            showlegend=False,
            xaxis={
                "showgrid": False,
                "linecolor": GRID,
                "type": "category",
                "tickangle": -35,
            },
            yaxis={
                "title": "Revenue",
                "gridcolor": GRID,
                "zerolinecolor": GRID,
                "tickprefix": "$",
            },
        )
        self.figure = fig

    def _build_summary(self) -> None:
        points: list[str] = [
            f"Fitted to {self.months_used} complete month(s) of revenue "
            f"({self.history_start} → {self.history_end}) worth {self.history_total_display}, "
            f"from {self.rows_used:,} cleaned rows.",
            f"{self.next_month_label} is estimated at {self.next_month_display} "
            f"({self.next_month_change_display} against {self.last_month_label} at {self.last_month_display}).",
            f"The next 3 months are estimated at {self.three_month_display} in total "
            f"({self.three_month_change_display} versus the last 3 complete months).",
            f"Trend direction is {self.trend_label.lower()} — {self.trend_detail}",
            f"Forecast confidence is {self.confidence_label.lower()}. {self.confidence_detail}",
        ]
        if self.band_available:
            points.append(
                f"{self.horizon_label} could land anywhere in {self.horizon_range} "
                "at a 95% prediction interval."
            )
        if self.partial_month_note:
            points.append(self.partial_month_note)
        if self.filters_applied:
            points.append(
                f"{self.filters_applied} dashboard filter(s) are applied, so this forecast "
                "covers only the rows currently in view."
            )
        points.append(
            "These are statistical estimates from your own history — not guaranteed outcomes. "
            "They assume the pattern in your file continues unchanged."
        )
        self.summary_points = points
