import reflex as rx


class DashboardTabState(rx.State):
    active: str = "overview"

    @rx.event
    def select_tab(self, value: str):
        self.active = value
