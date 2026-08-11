"""Executive report generation and data exports.

Every line that reaches the PDF is either a value already calculated by another
state (dashboard KPIs, profit, RFM, insights, forecast, data quality) or a
deterministic aggregation of the cleaned rows currently in view. Nothing is
estimated or invented here — if a figure isn't available, the report says so.
"""

import io
import logging
from datetime import datetime
from typing import TypedDict

import pandas as pd
import reflex as rx

from app.states.dashboard_state import (
    NOT_AVAILABLE,
    _col,
    _safe_div,
    _safe_float,
    _short,
    _to_datetime,
    _to_number,
    money,
)

REPORT_TITLE = "Business Analytics Report"
BRAND = "InsightSheet"

_KPI_ORDER: list[tuple[str, str]] = [
    ("revenue", "Total revenue"),
    ("orders", "Total orders"),
    ("customers", "Total customers"),
    ("aov", "Average order value"),
    ("growth", "Revenue growth"),
    ("repeat", "Repeat customer rate"),
]

_REPLACEMENTS: dict[str, str] = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2192": "->",
    "\u00b7": "-",
    "\u00f7": "/",
    "\u00d7": "x",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u03c3": " sigma",
    "\u2026": "...",
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
}


class ReportSection(TypedDict):
    key: str
    title: str
    icon: str
    summary: str
    lines: list[str]


class ReportKPI(TypedDict):
    label: str
    value: str
    caption: str
    available: bool


def _safe_text(value: object) -> str:
    """Make any string safe for reportlab paragraphs (XML + WinAnsi)."""
    text = str(value)
    for source, target in _REPLACEMENTS.items():
        text = text.replace(source, target)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _slug(name: str) -> str:
    stem = "".join(
        ch if ch.isalnum() else "_" for ch in str(name or "insightsheet")
    )
    stem = "_".join(part for part in stem.split("_") if part).lower()
    for suffix in ("_csv", "_xlsx", "_xls"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem or "insightsheet"


def _filter_records(
    records: list[dict[str, str]],
    mapping: dict[str, str],
    selections: dict[str, str],
    dim_columns: dict[str, str],
    start: str,
    end: str,
) -> tuple[pd.DataFrame | None, int]:
    """Return the cleaned rows that match the dashboard filters."""
    df = pd.DataFrame(records)
    if df.empty or len(df.columns) == 0:
        return (None, 0)
    applied = 0
    date_col = _col(mapping, "date")
    if date_col and date_col in df.columns:
        stamps = _to_datetime(df[date_col])
        start_stamp = pd.to_datetime(start, errors="coerce") if start else None
        end_stamp = pd.to_datetime(end, errors="coerce") if end else None
        keep = pd.Series(True, index=df.index)
        if start_stamp is not None and not pd.isna(start_stamp):
            keep &= stamps >= start_stamp
            applied += 1
        if end_stamp is not None and not pd.isna(end_stamp):
            keep &= stamps < end_stamp + pd.Timedelta(days=1)
            applied += 1
        df = df[keep]
    for key, value in selections.items():
        column = dim_columns.get(key, "")
        if not column or column not in df.columns:
            continue
        df = df[df[column].astype(str).str.strip() == value]
        applied += 1
    return (df, applied)


def _analysis_frame(
    frame: pd.DataFrame, mapping: dict[str, str]
) -> pd.DataFrame | None:
    """Attach parsed date/revenue columns for deterministic aggregation."""
    date_col = _col(mapping, "date")
    rev_col = _col(mapping, "revenue")
    if not date_col or not rev_col:
        return None
    if date_col not in frame.columns or rev_col not in frame.columns:
        return None
    work = frame.copy()
    work["_date"] = _to_datetime(work[date_col])
    work["_rev"] = _to_number(work[rev_col])
    work = work.dropna(subset=["_date", "_rev"])
    return work if not work.empty else None


def _rank(
    frame: pd.DataFrame, column: str, total: float, limit: int = 5
) -> list[tuple[str, float, float, int]]:
    work = frame.assign(
        _key=frame[column].astype(str).str.strip().replace("", "(blank)")
    )
    grouped = work.groupby("_key").agg(
        revenue=("_rev", "sum"), rows=("_rev", "size")
    )
    grouped = grouped.sort_values("revenue", ascending=False).head(limit)
    return [
        (
            _short(name, 40),
            _safe_float(row["revenue"]),
            _safe_div(_safe_float(row["revenue"]), total) * 100,
            int(_safe_float(row["rows"])),
        )
        for name, row in grouped.iterrows()
    ]


def _build_pdf(
    generated: str,
    source: str,
    period: str,
    rows_note: str,
    kpis: list[ReportKPI],
    sections: list[ReportSection],
) -> tuple[bytes, int]:
    """Render the executive report as a PDF and return (bytes, page count)."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    ink = colors.HexColor("#0f172a")
    muted = colors.HexColor("#64748b")
    accent = colors.HexColor("#2563eb")
    indigo = colors.HexColor("#4f46e5")
    line = colors.HexColor("#e2e8f0")
    soft = colors.HexColor("#f8fafc")

    base = getSampleStyleSheet()
    cover_brand = ParagraphStyle(
        "CoverBrand",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=34,
        textColor=accent,
        alignment=TA_CENTER,
    )
    cover_title = ParagraphStyle(
        "CoverTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        textColor=ink,
        alignment=TA_CENTER,
        spaceBefore=6,
    )
    cover_meta = ParagraphStyle(
        "CoverMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=17,
        textColor=muted,
        alignment=TA_CENTER,
    )
    heading = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=ink,
        spaceBefore=14,
        spaceAfter=2,
    )
    sub = ParagraphStyle(
        "SectionSub",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=13,
        textColor=muted,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=ink,
        leftIndent=10,
        bulletIndent=2,
        spaceAfter=3,
    )
    small = ParagraphStyle(
        "Small",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=muted,
    )

    story: list[object] = [
        Spacer(1, 58 * mm),
        Paragraph(_safe_text(BRAND), cover_brand),
        Paragraph(_safe_text(REPORT_TITLE), cover_title),
        Spacer(1, 10 * mm),
        Paragraph(f"Generated {_safe_text(generated)}", cover_meta),
        Paragraph(f"Source file: {_safe_text(source)}", cover_meta),
        Paragraph(f"Period analysed: {_safe_text(period)}", cover_meta),
        Paragraph(_safe_text(rows_note), cover_meta),
        Spacer(1, 16 * mm),
        Paragraph(
            _safe_text(
                "Every figure in this report is calculated from the cleaned rows of the "
                "uploaded spreadsheet. Nothing is estimated except where a section is "
                "explicitly labelled as a forecast."
            ),
            cover_meta,
        ),
        PageBreak(),
        Paragraph("KPI overview", heading),
        Paragraph(
            _safe_text(
                "Headline metrics for the rows currently in view. Metrics your file "
                "cannot support are marked as unavailable."
            ),
            sub,
        ),
    ]

    kpi_data: list[list[object]] = [
        [
            Paragraph("<b>Metric</b>", small),
            Paragraph("<b>Value</b>", small),
            Paragraph("<b>How it is calculated</b>", small),
        ]
    ]
    for card in kpis:
        kpi_data.append(
            [
                Paragraph(_safe_text(card["label"]), bullet),
                Paragraph(f"<b>{_safe_text(card['value'])}</b>", bullet),
                Paragraph(_safe_text(card["caption"]), small),
            ]
        )
    table = Table(
        kpi_data,
        colWidths=[48 * mm, 42 * mm, 80 * mm],
        hAlign="LEFT",
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), soft),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, line),
                ("GRID", (0, 0), (-1, -1), 0.4, line),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    for section in sections:
        story.append(Paragraph(_safe_text(section["title"]), heading))
        if section["summary"]:
            story.append(Paragraph(_safe_text(section["summary"]), sub))
        if not section["lines"]:
            story.append(Paragraph(_safe_text(NOT_AVAILABLE), bullet))
            continue
        for item in section["lines"]:
            story.append(
                Paragraph(_safe_text(item), bullet, bulletText="\u2022")
            )

    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            _safe_text(
                f"{BRAND} processed this spreadsheet in memory for this session only. "
                "No data was stored on disk or shared with a third party."
            ),
            small,
        )
    )

    def _decorate(canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 16 * mm, A4[0] - 20 * mm, 16 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(muted)
        canvas.drawString(20 * mm, 11 * mm, f"{BRAND} - {REPORT_TITLE}")
        canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Page {doc.page}")
        canvas.setFillColor(indigo)
        canvas.restoreState()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=22 * mm,
        title=f"{BRAND} {REPORT_TITLE}",
        author=BRAND,
    )
    doc.build(story, onFirstPage=_decorate, onLaterPages=_decorate)
    pages = int(getattr(doc, "page", 1) or 1)
    return (buffer.getvalue(), pages)


class ReportState(rx.State):
    """Builds the executive report and serves every export."""

    available: bool = False
    blocked_reason: str = "Upload a spreadsheet and map a date and revenue column to build a report."
    is_generating: bool = False
    exporting: str = ""
    report_ready: bool = False
    error_message: str = ""

    generated_at: str = ""
    source_label: str = ""
    period_label: str = ""
    rows_in_view: int = 0
    source_rows: int = 0
    filters_applied: int = 0
    section_count: int = 0
    page_count: int = 0
    pdf_size_kb: float = 0.0
    pdf_filename: str = "insightsheet_executive_report.pdf"

    kpis: list[ReportKPI] = []
    sections: list[ReportSection] = []

    _pdf: bytes = b""

    @rx.var
    def rows_note(self) -> str:
        if self.filters_applied:
            return (
                f"{self.rows_in_view:,} of {self.source_rows:,} cleaned rows "
                f"({self.filters_applied} filter(s) applied)"
            )
        return f"{self.rows_in_view:,} cleaned rows (no filters applied)"

    @rx.event
    async def prepare(self):
        """Refresh availability so the tab can show the right state on load."""
        from app.states.upload_state import UploadState

        try:
            upload = await self.get_state(UploadState)
            mapping = dict(upload.mapping or {})
            self.source_label = upload.source_label or upload.file_name
            self.source_rows = int(upload.clean_rows)
            if not upload.clean_records:
                self.available = False
                self.blocked_reason = (
                    "Upload a CSV or Excel export on the upload page and the report "
                    "will be written from the cleaned rows."
                )
            elif not _col(mapping, "date") or not _col(mapping, "revenue"):
                self.available = False
                self.blocked_reason = (
                    "Map a date column and a revenue column on the upload page so the "
                    "report has metrics to describe."
                )
            else:
                self.available = True
                self.blocked_reason = ""
        except Exception as e:
            logging.exception(f"Error preparing executive report: {e}")
            self.available = False
            self.blocked_reason = "Something went wrong reading your dataset. Re-upload the file and try again."

    @rx.event
    async def generate_report(self):
        self.error_message = ""
        self.is_generating = True
        yield
        try:
            await self._build()
        except Exception as e:
            logging.exception(f"Error generating executive report: {e}")
            self.report_ready = False
            self._pdf = b""
            self.error_message = (
                "We couldn't build the report from this dataset. Check the mapped date "
                "and revenue columns on the upload page, then try again."
            )
        finally:
            self.is_generating = False

    # ------------------------------------------------------------------
    # report assembly
    # ------------------------------------------------------------------

    async def _build(self) -> None:
        from app.states.dashboard_state import DashboardState
        from app.states.filter_state import FilterState
        from app.states.forecast_state import ForecastState
        from app.states.insight_state import InsightState
        from app.states.profit_state import ProfitState
        from app.states.rfm_state import RFMState
        from app.states.upload_state import UploadState

        upload = await self.get_state(UploadState)
        records = list(upload.clean_records or [])
        mapping = dict(upload.mapping or {})
        if not records:
            self.report_ready = False
            self._pdf = b""
            self.error_message = "There are no cleaned rows to report on yet. Upload a spreadsheet first."
            return
        if not _col(mapping, "date") or not _col(mapping, "revenue"):
            self.report_ready = False
            self._pdf = b""
            self.error_message = (
                "Map a date column and a revenue column on the upload page before "
                "generating the report."
            )
            return

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

        filtered, applied = _filter_records(
            records, mapping, selections, dim_columns, start, end
        )
        if filtered is None or filtered.empty:
            self.report_ready = False
            self._pdf = b""
            self.error_message = (
                "No rows match the filters currently applied, so there is nothing to "
                "report. Widen the date range or clear a filter and try again."
            )
            return

        dashboard = await self.get_state(DashboardState)
        profit = await self.get_state(ProfitState)
        rfm = await self.get_state(RFMState)
        insights = await self.get_state(InsightState)
        forecast = await self.get_state(ForecastState)

        frame = _analysis_frame(filtered, mapping)
        self.source_label = upload.source_label or upload.file_name
        self.source_rows = int(upload.clean_rows)
        self.rows_in_view = int(len(filtered))
        self.filters_applied = applied
        if frame is not None:
            self.period_label = (
                f"{frame['_date'].min().strftime('%b %d, %Y')} to "
                f"{frame['_date'].max().strftime('%b %d, %Y')}"
            )
        elif dashboard.period_start:
            self.period_label = (
                f"{dashboard.period_start} to {dashboard.period_end}"
            )
        else:
            self.period_label = "Not available from this dataset."

        kpis = self._kpi_rows(dashboard)
        sections: list[ReportSection] = [
            self._executive_section(dashboard),
            self._kpi_section(kpis),
            self._revenue_section(dashboard, profit),
            self._customer_section(dashboard, rfm, frame, mapping),
            self._product_section(dashboard, profit, frame, mapping),
            self._forecast_section(forecast),
            self._insight_section(insights),
            self._action_section(insights),
            self._quality_section(upload),
        ]

        generated = datetime.now().strftime("%B %d, %Y at %H:%M")
        pdf, pages = _build_pdf(
            generated,
            self.source_label or "Uploaded spreadsheet",
            self.period_label,
            self.rows_note,
            kpis,
            sections,
        )
        self._pdf = pdf
        self.kpis = kpis
        self.sections = sections
        self.section_count = len(sections)
        self.generated_at = generated
        self.page_count = pages
        self.pdf_size_kb = round(len(pdf) / 1024, 1)
        self.pdf_filename = f"{_slug(self.source_label)}_executive_report.pdf"
        self.report_ready = True
        self.error_message = ""

    def _kpi_rows(self, dashboard) -> list[ReportKPI]:
        lookup = {
            str(card["key"]): card for card in (dashboard.kpi_cards or [])
        }
        rows: list[ReportKPI] = []
        for key, label in _KPI_ORDER:
            if key == "growth":
                label = str(dashboard.growth_metric_label or label)
            card = lookup.get(key)
            if card is None:
                rows.append(
                    ReportKPI(
                        label=label,
                        value=NOT_AVAILABLE,
                        caption="This metric could not be calculated from the mapped columns.",
                        available=False,
                    )
                )
                continue
            rows.append(
                ReportKPI(
                    label=label,
                    value=str(card["value"]),
                    caption=str(card["caption"]),
                    available=bool(card["available"]),
                )
            )
        return rows

    def _section(
        self, key: str, title: str, icon: str, summary: str, lines: list[str]
    ) -> ReportSection:
        return ReportSection(
            key=key,
            title=title,
            icon=icon,
            summary=summary,
            lines=[line for line in lines if line],
        )

    def _executive_section(self, dashboard) -> ReportSection:
        lines: list[str] = []
        for card in dashboard.executive_highlights or []:
            if card["available"]:
                lines.append(
                    f"{card['label']}: {card['value']} - {card['detail']}"
                )
            else:
                lines.append(
                    f"{card['label']}: {NOT_AVAILABLE} {card['detail']}"
                )
        lines.extend(list(dashboard.summary_points or []))
        return self._section(
            "summary",
            "Executive summary",
            "file-text",
            "Headline facts calculated from the rows currently in view.",
            lines,
        )

    def _kpi_section(self, kpis: list[ReportKPI]) -> ReportSection:
        return self._section(
            "kpis",
            "KPI overview",
            "gauge",
            "Revenue, orders, customers, average order value, growth and repeat rate.",
            [
                f"{card['label']}: {card['value']} ({card['caption']})"
                for card in kpis
            ],
        )

    def _revenue_section(self, dashboard, profit) -> ReportSection:
        lines: list[str] = [
            f"Total revenue is {dashboard.total_revenue_display} across "
            f"{dashboard.order_count:,} orders ({dashboard.order_caption.lower()}).",
            f"Average order value is {dashboard.aov_display}.",
        ]
        if dashboard.best_period_label:
            lines.append(
                f"Strongest {dashboard.granularity.lower()} period is "
                f"{dashboard.best_period_label} at {dashboard.best_period_display}."
            )
        if dashboard.has_growth:
            lines.append(
                f"Latest month {dashboard.latest_month} produced "
                f"{dashboard.latest_revenue_display} from {dashboard.latest_orders:,} orders."
            )
            lines.append(
                f"{dashboard.comparison_label} is {dashboard.growth_display} - "
                f"{dashboard.growth_caption}."
            )
            if dashboard.partial_month_note:
                lines.append(dashboard.partial_month_note)
            if dashboard.large_change_detected:
                lines.append(
                    "Large revenue change detected: verify data completeness before "
                    "making business decisions."
                )
                for check in dashboard.large_change_checks or []:
                    flag = "needs review" if check["flagged"] else "passed"
                    lines.append(
                        f"Data check ({flag}) - {check['label']}: {check['detail']}"
                    )
                if dashboard.large_change_conclusion:
                    lines.append(dashboard.large_change_conclusion)
        elif dashboard.latest_month:
            lines.append(
                f"All rows fall in {dashboard.latest_month}, so month-over-month growth "
                "is not available from this selection."
            )
        for row in list(dashboard.month_history or [])[:12]:
            lines.append(
                f"{row['period']}: {row['revenue_display']} from {row['orders']:,} "
                f"order(s), month-over-month {row['change_display']}."
            )
        if profit.available:
            lines.append(
                f"Profit totals {profit.total_profit_signed} at a "
                f"{profit.margin_display} margin ({profit.method_formula})."
            )
            lines.append(
                f"Cost of sales is {profit.total_cost_display}, "
                f"{profit.cost_share:.1f}% of revenue, leaving "
                f"{profit.profit_per_order_display} of profit per order."
            )
        else:
            lines.append(f"Profit analysis: {profit.blocked_reason}")
        return self._section(
            "revenue",
            "Revenue analysis",
            "chart-line",
            "Revenue totals, trend and the profit behind them.",
            lines,
        )

    def _customer_section(
        self,
        dashboard,
        rfm,
        frame: pd.DataFrame | None,
        mapping: dict[str, str],
    ) -> ReportSection:
        cust_col = _col(mapping, "customer")
        if not dashboard.has_customer_data or not cust_col:
            return self._section(
                "customers",
                "Customer analysis",
                "users-round",
                "Customer behaviour could not be measured.",
                [
                    "No customer column is mapped, so retention, repeat buying and "
                    "customer ranking are not available from this dataset."
                ],
            )
        lines: list[str] = [
            f"{dashboard.customer_count:,} distinct customers appear in the mapped "
            "customer column.",
            f"Retention rate is {dashboard.retention_rate:.1f}% - "
            f"{dashboard.active_customers:,} active, {dashboard.at_risk_customers:,} at risk, "
            f"{dashboard.inactive_customers:,} potentially inactive as of "
            f"{dashboard.reference_date}.",
            "Historical Revenue from Potentially Inactive Customers: "
            f"{dashboard.inactive_revenue_display}. This represents historical revenue "
            "associated with customers who have been inactive for 60+ days. It is not a "
            "prediction of future revenue loss.",
            f"Repeat customer rate is {dashboard.repeat_rate:.1f}% "
            f"({dashboard.repeat_customers:,} customers ordered more than once).",
            f"Revenue per customer averages {money(dashboard.revenue_per_customer)}.",
        ]
        for bucket in dashboard.inactivity_buckets or []:
            lines.append(
                f"Inactive {bucket['label']}: {bucket['customers']:,} customer(s) with "
                f"{bucket['revenue_display']} of historical revenue "
                f"({bucket['share_display']} of the potentially inactive total)."
            )
        if dashboard.has_concentration:
            lines.append(
                f"Customer concentration is {dashboard.concentration_level.lower()} - top 1 "
                f"customer {dashboard.top1_share:.1f}% ({dashboard.top1_revenue_display}), "
                f"top {dashboard.top5_count} {dashboard.top5_share:.1f}% "
                f"({dashboard.top5_revenue_display}), top {dashboard.top10_count} "
                f"{dashboard.top10_share:.1f}% ({dashboard.top10_revenue_display}) of revenue."
            )
            lines.append(dashboard.concentration_detail)
        else:
            lines.append(
                "Customer concentration could not be measured from this dataset."
            )
        if dashboard.clv_available:
            lines.append(
                f"Customer lifetime value is {money(dashboard.clv_estimate)} "
                f"({dashboard.clv_caption})."
            )
        if frame is not None and cust_col in frame.columns:
            total = _safe_float(frame["_rev"].sum())
            for name, value, share, rows in _rank(frame, cust_col, total):
                lines.append(
                    f"Top customer {name}: {money(value)} ({share:.1f}% of revenue) "
                    f"across {rows:,} row(s)."
                )
        if rfm.available:
            lines.append(
                f"Customer Intelligence - RFM Analysis: {rfm.customer_total:,} customers were "
                f"scored on recency, frequency and monetary value using "
                f"{rfm.reference_date} as the latest valid transaction date."
            )
            if rfm.scoring_note:
                lines.append(rfm.scoring_note)
            for segment in list(rfm.segments or [])[:10]:
                lines.append(
                    f"Segment {segment['name']}: {segment['customers']:,} customers "
                    f"({segment['share_display']}), {segment['revenue_display']} of revenue "
                    f"({segment['revenue_share_display']}). {segment['rule']}."
                )
            for action in list(rfm.recommendations or []):
                lines.append(
                    f"RFM recommendation ({action['segment']}, {action['priority']} priority) - "
                    f"{action['title']}: {action['detail']} Scope: {action['scope']}."
                )
        else:
            lines.append(
                f"Customer Intelligence - RFM Analysis: {rfm.blocked_reason}"
            )
        return self._section(
            "customers",
            "Customer analysis",
            "users-round",
            "Retention, repeat buying, top accounts and segments.",
            lines,
        )

    def _product_section(
        self,
        dashboard,
        profit,
        frame: pd.DataFrame | None,
        mapping: dict[str, str],
    ) -> ReportSection:
        prod_col = _col(mapping, "product")
        if not dashboard.has_product_data or not prod_col:
            return self._section(
                "products",
                "Product analysis",
                "package",
                "Product performance could not be measured.",
                [
                    "No product or category column is mapped, so revenue and margin "
                    "cannot be broken down by product."
                ],
            )
        lines: list[str] = [
            f"{dashboard.product_count:,} distinct products or categories appear in the "
            "mapped product column."
        ]
        if frame is not None and prod_col in frame.columns:
            total = _safe_float(frame["_rev"].sum())
            for name, value, share, rows in _rank(frame, prod_col, total, 8):
                lines.append(
                    f"{name}: {money(value)} ({share:.1f}% of revenue) across "
                    f"{rows:,} row(s)."
                )
        if profit.available and profit.has_margin_table:
            lines.append(
                f"Margin range by {profit.margin_table_label.lower()}: "
                f"{profit.best_margin_display} ({profit.best_margin_name}) down to "
                f"{profit.worst_margin_display} ({profit.worst_margin_name})."
            )
            for row in list(profit.margin_table or [])[:8]:
                lines.append(
                    f"{row['name']}: revenue {row['revenue_display']}, cost "
                    f"{row['cost_display']}, profit {row['profit_display']}, margin "
                    f"{row['margin_display']}, share of profit {row['share_display']}."
                )
            if profit.loss_rows:
                lines.append(
                    f"{profit.loss_rows:,} row(s) sold below cost, losing "
                    f"{profit.loss_amount_display}."
                )
        elif not profit.available:
            lines.append(f"Product margins: {profit.blocked_reason}")
        return self._section(
            "products",
            "Product analysis",
            "package",
            "What sells, what it earns and where margin sits.",
            lines,
        )

    def _forecast_section(self, forecast) -> ReportSection:
        if not forecast.available:
            return self._section(
                "forecast",
                "Forecast",
                "trending-up",
                "No forecast is included.",
                [
                    forecast.blocked_reason,
                    "Forecasts are only shown when your own history can support them.",
                ]
                + list(forecast.missing_hints or []),
            )
        lines: list[str] = [
            "The figures in this section are statistical estimates, not guaranteed outcomes.",
            f"Fitted to {forecast.months_used} complete month(s) of revenue "
            f"({forecast.history_start} to {forecast.history_end}) worth "
            f"{forecast.history_total_display}.",
            f"{forecast.next_month_label} is estimated at {forecast.next_month_display} "
            f"({forecast.next_month_change_display} versus {forecast.last_month_label} at "
            f"{forecast.last_month_display}).",
            f"Next 3 months estimated at {forecast.three_month_display} in total "
            f"({forecast.three_month_change_display}). {forecast.three_month_basis}.",
            f"{forecast.horizon_label} estimated at {forecast.horizon_total_display} "
            f"(95% range {forecast.horizon_range}).",
            f"Trend direction is {forecast.trend_label.lower()} at "
            f"{forecast.trend_per_month_display} per month.",
            f"Forecast confidence is {forecast.confidence_label.lower()}. "
            f"{forecast.confidence_detail}",
            forecast.method_note,
        ]
        for row in list(forecast.forecast_rows or []):
            lines.append(
                f"{row['month']}: {row['value_display']} (95% range "
                f"{row['range_display']}, change {row['change_display']})."
            )
        if forecast.partial_month_note:
            lines.append(forecast.partial_month_note)
        return self._section(
            "forecast",
            "Forecast (estimates)",
            "trending-up",
            "Projected monthly revenue with prediction ranges.",
            lines,
        )

    def _insight_section(self, insights) -> ReportSection:
        if not insights.available:
            return self._section(
                "insights",
                "Key insights",
                "lightbulb",
                "No automated insights are included.",
                [insights.blocked_reason] + list(insights.missing_hints or []),
            )
        lines = [
            f"{item['category']} - {item['title']}: {item['detail']} "
            f"({item['metric_label']}: {item['metric_value']})"
            for item in insights.insights or []
        ]
        return self._section(
            "insights",
            "Key insights",
            "lightbulb",
            insights.basis_note,
            lines,
        )

    def _action_section(self, insights) -> ReportSection:
        if not insights.available:
            return self._section(
                "actions",
                "Recommended actions",
                "list-checks",
                "No actions are suggested.",
                [
                    "Recommended actions are only written from detected patterns in your "
                    "own rows, and none could be measured."
                ],
            )
        lines = [
            f"[{item['priority']} priority] {item['title']}: {item['detail']} "
            f"({item['basis']})"
            for item in insights.suggestions or []
        ]
        return self._section(
            "actions",
            "Recommended actions",
            "list-checks",
            "Suggestions derived from the patterns above - review each against what you know.",
            lines,
        )

    def _quality_section(self, upload) -> ReportSection:
        lines: list[str] = [
            f"Data quality score is {upload.quality_score}/100 ({upload.quality_band}). "
            f"{upload.quality_band_detail}",
            f"{upload.clean_rows:,} of {upload.raw_rows:,} rows were kept across "
            f"{len(upload.columns)} column(s).",
        ]
        for part in upload.score_breakdown or []:
            lines.append(
                f"{part['label']}: {part['points']} of {part['max_points']} points - "
                f"{part['detail']}."
            )
        lines.append(
            f"{upload.missing_cells:,} of {upload.total_cells:,} cells were empty or "
            f"unreadable ({upload.missing_share_display}); "
            f"{upload.invalid_date_cells:,} invalid date(s) and "
            f"{upload.invalid_number_cells:,} invalid number(s) were found, with "
            f"{upload.outlier_cells:,} numeric outlier(s) flagged but kept."
        )
        for op in upload.cleaning_operations or []:
            if op["applied"]:
                lines.append(f"{op['title']} ({op['count']}): {op['detail']}")
        for step in upload.cleaning_log or []:
            lines.append(f"{step['title']}: {step['detail']}")
        return self._section(
            "quality",
            "Data quality and cleaning summary",
            "shield-check",
            "How trustworthy these numbers are and exactly what was changed.",
            lines,
        )

    # ------------------------------------------------------------------
    # exports
    # ------------------------------------------------------------------

    @rx.event
    def download_pdf(self):
        if not self._pdf:
            self.error_message = (
                "Generate the executive report first, then download the PDF."
            )
            return
        self.error_message = ""
        return rx.download(data=self._pdf, filename=self.pdf_filename)

    @rx.event
    async def download_csv(self):
        from app.states.upload_state import UploadState

        self.error_message = ""
        self.exporting = "csv"
        yield
        try:
            upload = await self.get_state(UploadState)
            records = list(upload.clean_records or [])
            if not records:
                self.error_message = "There are no cleaned rows to export yet."
                return
            frame = pd.DataFrame(records)
            data = frame.to_csv(index=False).encode("utf-8-sig")
            name = (
                f"{_slug(upload.source_label or upload.file_name)}_cleaned.csv"
            )
            yield rx.download(data=data, filename=name)
        except Exception as e:
            logging.exception(f"Error exporting cleaned CSV: {e}")
            self.error_message = "We couldn't build the cleaned CSV. Re-upload the file and try again."
        finally:
            self.exporting = ""

    @rx.event
    async def download_excel(self):
        from app.states.upload_state import UploadState

        self.error_message = ""
        self.exporting = "excel"
        yield
        try:
            upload = await self.get_state(UploadState)
            records = list(upload.clean_records or [])
            if not records:
                self.error_message = "There are no cleaned rows to export yet."
                return
            frame = pd.DataFrame(records)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                frame.to_excel(writer, index=False, sheet_name="Cleaned data")
            name = (
                f"{_slug(upload.source_label or upload.file_name)}_cleaned.xlsx"
            )
            yield rx.download(data=buffer.getvalue(), filename=name)
        except Exception as e:
            logging.exception(f"Error exporting cleaned Excel: {e}")
            self.error_message = "We couldn't build the Excel workbook. Re-upload the file and try again."
        finally:
            self.exporting = ""

    @rx.event
    async def download_filtered(self):
        from app.states.filter_state import FilterState
        from app.states.upload_state import UploadState

        self.error_message = ""
        self.exporting = "filtered"
        yield
        try:
            upload = await self.get_state(UploadState)
            records = list(upload.clean_records or [])
            mapping = dict(upload.mapping or {})
            if not records:
                self.error_message = "There are no cleaned rows to export yet."
                return
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
            frame, applied = _filter_records(
                records, mapping, selections, dim_columns, start, end
            )
            if frame is None or frame.empty:
                self.error_message = (
                    "No rows match the filters currently applied, so there is nothing "
                    "to export. Widen the date range or clear a filter."
                )
                return
            data = frame.to_csv(index=False).encode("utf-8-sig")
            suffix = "filtered" if applied else "dashboard"
            name = f"{_slug(upload.source_label or upload.file_name)}_{suffix}_data.csv"
            yield rx.download(data=data, filename=name)
        except Exception as e:
            logging.exception(f"Error exporting filtered dashboard data: {e}")
            self.error_message = "We couldn't build the filtered export. Adjust your filters and try again."
        finally:
            self.exporting = ""
