from backend.core.analytics_pro_engine import build_analytics_dashboard

class AnalyticsProService:
    def dashboard(self, picks):
        return build_analytics_dashboard(picks)
