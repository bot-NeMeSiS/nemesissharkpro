
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TZ = os.getenv("APP_TIMEZONE", "Europe/Madrid")
MAX_FUTURE_DAYS = int(os.getenv("MAX_FUTURE_DAYS", "45"))

def get_app_timezone():
    try:
        return ZoneInfo(os.getenv("DISPLAY_TIMEZONE", DEFAULT_TZ))
    except Exception:
        return ZoneInfo("Europe/Madrid")

def now_madrid():
    return datetime.now(get_app_timezone())

def parse_api_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if not raw:
            return None
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
        except Exception:
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
                try:
                    dt = datetime.strptime(str(value), fmt)
                    break
                except Exception:
                    pass
            if dt is None:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(get_app_timezone())

def is_valid_match_datetime(dt):
    if not dt:
        return False
    now = now_madrid()
    if os.getenv("BLOCK_FAKE_FUTURE_YEARS", "true").lower() == "true" and dt.year > now.year + 1:
        return False
    return (now - timedelta(days=3)) <= dt <= (now + timedelta(days=MAX_FUTURE_DAYS))

def format_match_datetime(value):
    dt = parse_api_datetime(value)
    if not dt:
        return {"valid": False, "date_label": "Fecha no disponible", "time_label": "--:--", "full_label": "Fecha no disponible", "relative_label": "Sin horario confirmado", "iso": None}
    valid = is_valid_match_datetime(dt)
    now = now_madrid()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    dias = ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]
    meses = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
    if dt.date() == today:
        date_label = "HOY"
    elif dt.date() == tomorrow:
        date_label = "MAÑANA"
    else:
        date_label = f"{dias[dt.weekday()]} {dt.day} {meses[dt.month-1]}"
    time_label = dt.strftime("%H:%M")
    minutes = int((dt - now).total_seconds() // 60)
    if -130 <= minutes <= 130:
        relative = "Live / en juego"
    elif minutes > 0:
        relative = f"Empieza en {minutes} min" if minutes < 60 else (f"Empieza en {minutes//60} h" if minutes < 1440 else f"Empieza en {minutes//1440} días")
    else:
        relative = "Finalizado / reciente"
    return {"valid": valid, "date_label": date_label, "time_label": time_label, "full_label": dt.strftime("%d/%m/%Y · %H:%M h Madrid"), "relative_label": relative, "iso": dt.isoformat(), "year": dt.year}

def normalize_match_time_payload(match):
    if not isinstance(match, dict):
        return match
    raw = match.get("commence_time") or match.get("start_time") or match.get("match_time") or match.get("date") or match.get("datetime")
    f = format_match_datetime(raw)
    match.update({
        "display_date": f["date_label"], "display_time": f["time_label"],
        "display_datetime": f["full_label"], "display_relative": f["relative_label"],
        "time_valid": f["valid"], "timezone": "Europe/Madrid"
    })
    return match

def filter_invalid_matches(matches):
    if not isinstance(matches, list):
        return matches
    out = []
    for m in matches:
        item = normalize_match_time_payload(m)
        if os.getenv("HIDE_INVALID_MATCH_DATES", "true").lower() == "true" and isinstance(item, dict) and not item.get("time_valid", True):
            continue
        out.append(item)
    return out

def get_time_v82_status():
    n = now_madrid()
    return {"status": "TIMEZONE MADRID ACTIVO", "timezone": str(get_app_timezone()), "now": n.isoformat(), "display_now": n.strftime("%d/%m/%Y · %H:%M h Madrid"), "max_future_days": MAX_FUTURE_DAYS}
