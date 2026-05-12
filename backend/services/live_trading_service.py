from backend.core.live_trading_engine import build_live_trading_reading, build_live_center

class LiveTradingService:
    def analyze(self, match):
        return build_live_trading_reading(match)

    def center(self, matches):
        return build_live_center(matches)
