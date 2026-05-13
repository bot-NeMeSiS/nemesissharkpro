
from datetime import datetime

def build_live_event(event):
    return {
        "minute": event.get("minute") or "LIVE",
        "type": event.get("type") or "INFO",
        "text": event.get("text") or "Evento live recibido",
        "team": event.get("team") or "N/A"
    }

def build_live_center_pro(matches):
    matches = matches or []
    cards = []
    for m in matches:
        pressure = float(m.get("pressure") or m.get("momentum_score") or 0)
        if pressure >= 85:
            signal = "HIGH_PRESSURE"
        elif pressure >= 70:
            signal = "VALUE_WATCH"
        elif pressure >= 55:
            signal = "LIVE_WATCH"
        else:
            signal = "NO_SIGNAL"

        cards.append({
            "match": m.get("match") or f"{m.get('home_team','Local')} vs {m.get('away_team','Visitante')}",
            "minute": m.get("minute") or "LIVE",
            "scoreline": m.get("scoreline") or "N/A",
            "pressure": pressure,
            "signal": signal,
            "events": [build_live_event(e) for e in m.get("events", [])],
            "reading": f"Señal live {signal} con presión {pressure}.",
        })

    return {
        "version": "V128_LIVE_CENTER_PRO",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(cards),
        "cards": cards,
        "empty_state": not bool(cards),
        "no_fake_policy": True
    }
