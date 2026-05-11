
from datetime import datetime

def build_live_snapshot():
    return {
        "status": "LIVE",
        "updated_at": datetime.utcnow().isoformat(),
        "live_matches": 4,
        "high_value_alerts": 2,
        "momentum_changes": 3
    }
