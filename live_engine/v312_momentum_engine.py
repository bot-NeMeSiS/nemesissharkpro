
from datetime import datetime, timezone
import re

LIVE_WORDS = {"EN DIRECTO", "LIVE", "1H", "2H", "DESCANSO", "HT"}
FINISHED_WORDS = {"FINALIZADO", "FT", "FINISHED"}


def _num(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _minute(value):
    text = str(value or "")
    m = re.search(r"(\d{1,3})", text)
    if not m:
        return None
    return max(0, min(130, int(m.group(1))))


def _status(row):
    return str(row.get("live_status") or "PROGRAMADO").upper().strip()


def _data_health(row):
    points = 0
    if row.get("title"): points += 1
    if row.get("league"): points += 1
    if row.get("kickoff_time") or row.get("live_minute"): points += 1
    if row.get("live_score"): points += 1
    if row.get("external_event_id") or row.get("source"): points += 1
    if row.get("pick") or row.get("cuota"): points += 1
    if points >= 5:
        return "OK"
    if points >= 3:
        return "WATCH"
    return "LOW DATA"


def _momentum(row):
    status = _status(row)
    score = _num(row.get("score"), 0)
    ev = _num(row.get("ev"), 0)
    minute = _minute(row.get("live_minute"))
    base = 28
    if status in LIVE_WORDS:
        base += 28
    elif status in FINISHED_WORDS:
        base += 8
    else:
        base += 12
    base += min(24, max(0, score - 60) * 0.6)
    if ev > 0:
        base += min(12, ev * 1.2)
    if minute is not None:
        if 35 <= minute <= 55 or 70 <= minute <= 88:
            base += 10
        elif minute >= 89:
            base += 6
    if row.get("live_score"):
        base += 5
    return int(max(0, min(99, round(base))))


def _trigger(row, momentum):
    status = _status(row)
    minute = _minute(row.get("live_minute"))
    ev = _num(row.get("ev"), 0)
    score = _num(row.get("score"), 0)
    if status in LIVE_WORDS and momentum >= 78:
        return "HOT", "Partido vivo con señal fuerte"
    if ev >= 6 and score >= 80:
        return "VALUE", "Valor alto detectado"
    if minute is not None and (35 <= minute <= 45 or 75 <= minute <= 88):
        return "TIMING", "Minuto sensible para observar"
    if _data_health(row) == "LOW DATA":
        return "LOW DATA", "Faltan datos para decidir"
    return "WATCH", "Buen partido para seguimiento"


def build_live_engine_snapshot_v312(rows):
    enriched = []
    for row in rows or []:
        r = dict(row)
        m = _momentum(r)
        trigger, reason = _trigger(r, m)
        health = _data_health(r)
        r.update({
            "momentum": m,
            "trigger": trigger,
            "trigger_reason": reason,
            "data_health": health,
            "client_action": _client_action(trigger, health),
            "snapshot_key": f"v312-{r.get('id','x')}-{m}-{trigger}",
        })
        enriched.append(r)
    enriched.sort(key=lambda x: (x.get("trigger") != "HOT", -int(x.get("momentum", 0)), x.get("title", "")))
    hot = [x for x in enriched if x.get("trigger") == "HOT"]
    watch = [x for x in enriched if x.get("trigger") in ("WATCH", "TIMING", "VALUE")]
    low = [x for x in enriched if x.get("data_health") == "LOW DATA"]
    avg = int(round(sum(x.get("momentum",0) for x in enriched) / max(1, len(enriched))))
    headline = "Live Engine esperando partidos reales cacheados."
    if hot:
        headline = f"{len(hot)} partido(s) HOT ahora mismo. Prioridad máxima de seguimiento."
    elif watch:
        headline = f"{len(watch)} partido(s) en zona WATCH/VALUE. Buen momento para preparar decisiones."
    elif enriched:
        headline = "Hay partidos disponibles, pero el motor recomienda esperar más señal."
    return {
        "ok": True,
        "version": "V312",
        "mode": "cache-first-real-live-engine",
        "touches_api": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "headline": headline,
            "momentum_avg": avg,
            "hot_count": len(hot),
            "watch_count": len(watch),
            "low_data_count": len(low),
            "data_health": "OK" if enriched and len(low) < len(enriched) else ("LOW DATA" if not enriched or len(low) else "WATCH"),
        },
        "matches": enriched,
        "timeline": _timeline(enriched),
        "snapshots": [{"key": x["snapshot_key"], "match_id": x.get("id"), "momentum": x.get("momentum"), "trigger": x.get("trigger")} for x in enriched[:8]],
    }


def _client_action(trigger, health):
    if health == "LOW DATA":
        return "Esperar datos: no tomar decisión todavía."
    if trigger == "HOT":
        return "Abrir Match Center y vigilar cuota/marcador."
    if trigger == "VALUE":
        return "Revisar pick, cuota y stake responsable."
    if trigger == "TIMING":
        return "Seguir en directo: minuto sensible."
    return "Guardar en seguimiento."


def _timeline(items):
    if not items:
        return [{"label": "Sin datos live", "text": "El motor queda preparado sin gastar API."}]
    events = []
    for item in items[:6]:
        events.append({
            "label": item.get("trigger", "WATCH"),
            "text": f"{item.get('title','Partido')} · momentum {item.get('momentum',0)}/99 · {item.get('client_action','Seguir')}",
        })
    return events
