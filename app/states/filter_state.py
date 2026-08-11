"""Global dashboard filters.

Filter dimensions are only offered when a matching column actually exists in
the cleaned file (either mapped by the user or detected by the profiler), so a
filter can never invent a dimension the dataset doesn't have.
"""

import logging
from typing import TypedDict

import pandas as pd
import reflex as rx

from app.states.dashboard_state import _to_datetime

MAX_OPTIONS = 200


class FilterDimension(TypedDict):
    key: str
    label: str
    column: str
    icon: str
    values: list[str]


def _norm(name: object) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def _find(columns: list[str], keywords: tuple[str, ...], used: set[str]) -> str:
    for keyword in keywords:
        for col in columns:
            if col in used:
                continue
            if keyword in _norm(col):
                return col
    return ""


def _mapped(mapping: dict[str, str] | None, key: str) -> str:
    if not isinstance(mapping, dict):
        return ""
    value = mapping.get(key)
    return str(value).strip() if value is not None else ""


def _options(frame: pd.DataFrame, column: str) -> list[str]:
    values = frame[column].astype(str).str.strip()
    values = values[values.str.len() > 0]
    values = values[~values.str.lower().isin(("nan", "none", "null"))]
    unique = sorted(set(values.tolist()), key=lambda v: v.lower())
    return unique


class FilterState(rx.State):
    signature: str = ""
    ready: bool = False
    dimensions: list[FilterDimension] = []
    selections: dict[str, str] = {}
    form_key: int = 0

    date_available: bool = False
    date_column: str = ""
    date_min: str = ""
    date_max: str = ""
    start_date: str = ""
    end_date: str = ""

    @rx.var
    def has_dimensions(self) -> bool:
        return len(self.dimensions) > 0

    @rx.var
    def dimension_count(self) -> int:
        return len(self.dimensions)

    @rx.var
    def date_range_changed(self) -> bool:
        if not self.date_available:
            return False
        return (
            self.start_date != self.date_min or self.end_date != self.date_max
        )

    @rx.var
    def has_active(self) -> bool:
        return bool(
            any(value for value in self.selections.values())
            or self.date_range_changed
        )

    @rx.var
    def active_labels(self) -> list[str]:
        labels: list[str] = []
        if self.date_range_changed:
            labels.append(f"Dates: {self.start_date} → {self.end_date}")
        for dim in self.dimensions:
            value = self.selections.get(dim["key"], "")
            if value:
                labels.append(f"{dim['label']}: {value}")
        return labels

    @rx.var
    def summary_line(self) -> str:
        if not self.date_available and not self.dimensions:
            return "No filterable columns were found in this file."
        parts: list[str] = []
        if self.date_available:
            parts.append(f"date range from “{self.date_column}”")
        if self.dimensions:
            names = ", ".join(f"“{d['column']}”" for d in self.dimensions)
            parts.append(f"values from {names}")
        return f"Filtering by {' and '.join(parts)}."

    @rx.event
    async def build_filters(self):
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        business = {
            str(item["role"]): str(item["column"])
            for item in upload.business_columns
        }
        signature = (
            f"{upload.file_name}|{upload.clean_rows}|"
            f"{sorted((k, v) for k, v in mapping.items())}"
        )
        if not records:
            self._clear()
            return
        try:
            self._build(records, mapping, business, signature)
        except Exception as e:
            logging.exception(f"Error building dashboard filters: {e}")
            self._clear()

    def _clear(self) -> None:
        self.signature = ""
        self.ready = False
        self.dimensions = []
        self.selections = {}
        self.date_available = False
        self.date_column = ""
        self.date_min = ""
        self.date_max = ""
        self.start_date = ""
        self.end_date = ""
        self.form_key += 1

    def _build(
        self,
        records: list[dict[str, str]],
        mapping: dict[str, str],
        business: dict[str, str],
        signature: str,
    ) -> None:
        mapping = mapping if isinstance(mapping, dict) else {}
        business = business if isinstance(business, dict) else {}
        df = pd.DataFrame(records)
        if df.empty or len(df.columns) == 0:
            self._clear()
            return
        columns = [str(c) for c in df.columns]
        used: set[str] = set()

        date_col = _mapped(mapping, "date")
        if date_col and date_col in columns:
            stamps = _to_datetime(df[date_col]).dropna()
            if not stamps.empty:
                self.date_available = True
                self.date_column = date_col
                self.date_min = stamps.min().strftime("%Y-%m-%d")
                self.date_max = stamps.max().strftime("%Y-%m-%d")
            else:
                self.date_available = False
                self.date_column = ""
                self.date_min = ""
                self.date_max = ""
        else:
            self.date_available = False
            self.date_column = ""
            self.date_min = ""
            self.date_max = ""

        product_col = _mapped(mapping, "product") or str(
            business.get("Product", "") or ""
        )
        customer_col = _mapped(mapping, "customer") or str(
            business.get("Customer", "") or ""
        )
        if product_col:
            used.add(product_col)
        if customer_col:
            used.add(customer_col)

        category_col = _find(columns, ("category", "segment", "type"), used)
        if category_col:
            used.add(category_col)
        region_col = str(business.get("Region", "") or "") or _find(
            columns,
            (
                "region",
                "country",
                "state",
                "province",
                "city",
                "territory",
                "market",
                "zone",
            ),
            used,
        )
        if region_col:
            used.add(region_col)
        sales_col = str(business.get("Salesperson", "") or "") or _find(
            columns,
            (
                "salesperson",
                "sales rep",
                "sales person",
                "rep",
                "agent",
                "owner",
                "employee",
                "manager",
            ),
            used,
        )
        if sales_col:
            used.add(sales_col)

        candidates: list[tuple[str, str, str, str]] = [
            ("product", "Product", "package", product_col),
            ("category", "Category", "tags", category_col),
            ("customer", "Customer", "user-round", customer_col),
            ("region", "Region", "map-pin", region_col),
            ("salesperson", "Salesperson", "briefcase", sales_col),
        ]

        dimensions: list[FilterDimension] = []
        for key, label, icon, column in candidates:
            if not column or column not in columns:
                continue
            values = _options(df, column)
            if len(values) < 2 or len(values) > MAX_OPTIONS:
                continue
            dimensions.append(
                FilterDimension(
                    key=key,
                    label=label,
                    column=column,
                    icon=icon,
                    values=values,
                )
            )

        keep = self.signature == signature
        previous = dict(self.selections) if keep else {}
        selections: dict[str, str] = {}
        for dim in dimensions:
            chosen = previous.get(dim["key"], "")
            selections[dim["key"]] = chosen if chosen in dim["values"] else ""
        self.selections = selections
        self.dimensions = dimensions

        if self.date_available:
            if (
                keep
                and self.start_date
                and self.date_min <= self.start_date <= self.date_max
            ):
                pass
            else:
                self.start_date = self.date_min
            if (
                keep
                and self.end_date
                and self.date_min <= self.end_date <= self.date_max
            ):
                pass
            else:
                self.end_date = self.date_max
        else:
            self.start_date = ""
            self.end_date = ""

        if not keep:
            self.form_key += 1
        self.signature = signature
        self.ready = bool(self.date_available or dimensions)

    @rx.event
    def select_dimension(self, key: str, value: str):
        from app.states.dashboard_state import DashboardState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState

        self.selections[key] = value
        yield DashboardState.compute_metrics
        yield InsightState.compute_insights
        yield ForecastState.compute_forecast

    @rx.event
    def set_start(self, value: str):
        from app.states.dashboard_state import DashboardState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState

        self.start_date = value
        if self.end_date and value and value > self.end_date:
            self.end_date = value
            self.form_key += 1
        yield DashboardState.compute_metrics
        yield InsightState.compute_insights
        yield ForecastState.compute_forecast

    @rx.event
    def set_end(self, value: str):
        from app.states.dashboard_state import DashboardState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState

        self.end_date = value
        if self.start_date and value and value < self.start_date:
            self.start_date = value
            self.form_key += 1
        yield DashboardState.compute_metrics
        yield InsightState.compute_insights
        yield ForecastState.compute_forecast

    @rx.event
    def reset_filters(self):
        from app.states.dashboard_state import DashboardState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState

        self.selections = {key: "" for key in self.selections}
        self.start_date = self.date_min
        self.end_date = self.date_max
        self.form_key += 1
        yield DashboardState.compute_metrics
        yield InsightState.compute_insights
        yield ForecastState.compute_forecast
