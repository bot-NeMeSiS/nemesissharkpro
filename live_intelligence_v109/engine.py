
from datetime import datetime

def build_live_signal(match):
    home_pressure = match.get("home_pressure", 50)
    away_pressure = match.get("away_pressure", 50)

    momentum = "LOCAL"
    if away_pressure > home_pressure:
        momentum = "VISITANTE"

    shark_score = min(95, int((home_pressure + away_pressure) / 2))

    return {
        "match": match.get("match", "Partido live"),
        "minute": match.get("minute", 0),
        "momentum": momentum,
        "shark_score": shark_score,
        "signal": "OVER 1.5 LIVE" if shark_score >= 70 else "NO ENTRY",
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

def demo_live_feed():
    matches = [
        {"match": "Real Madrid vs Barcelona", "minute": 61, "home_pressure": 82, "away_pressure": 58},
        {"match": "Liverpool vs Arsenal", "minute": 33, "home_pressure": 66, "away_pressure": 73},
    ]
    return [build_live_signal(m) for m in matches]
