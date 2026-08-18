import reflex as rx

from app.pages.about import about_page
from app.pages.dashboard import dashboard_page
from app.pages.data_quality import data_quality_page
from app.pages.feedback import feedback_page
from app.pages.pricing import pricing_page
from app.pages.upload import upload_page
from app.razorpay_webhook import webhook_api
from app.states.ask_state import AskState
from app.states.dashboard_state import DashboardState
from app.states.filter_state import FilterState
from app.states.forecast_state import ForecastState
from app.states.insight_state import InsightState
from app.states.profit_state import ProfitState
from app.states.report_state import ReportState
from app.states.rfm_state import RFMState


def index() -> rx.Component:
    return upload_page()


app = rx.App(
    api_transformer=webhook_api,
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.meta(
            name="google-site-verification",
            content="XrNMyDksjgrV8Yac6jj-dWw99yxQjvI_317dBMmP2Ys",
        ),
        rx.el.style(".rx-built-with-reflex { display: none !important; }"),
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
app.add_page(
    dashboard_page,
    route="/dashboard",
    on_load=[
        FilterState.build_filters,
        DashboardState.compute_metrics,
        ProfitState.compute_profit,
        RFMState.compute_rfm,
        InsightState.compute_insights,
        ForecastState.compute_forecast,
        AskState.prepare,
        ReportState.prepare,
    ],
)
app.add_page(data_quality_page, route="/data-quality")
app.add_page(feedback_page, route="/feedback")
app.add_page(pricing_page, route="/pricing")
app.add_page(about_page, route="/about")
