
from datetime import datetime

def _get_feed(force=False):
    try:
        from core.real_core_engine import RealCoreEngine
        return RealCoreEngine.fetch(force=force)
    except Exception as exc:
        return {
            "ok": False,
            "source": "none",
            "message": "Real Core no disponible. Modo seguro sin demos.",
            "error": str(exc),
            "matches": [],
            "picks": [],
            "buckets": {"live": [], "today": [], "upcoming": []},
            "counts": {"total": 0, "live": 0, "today": 0, "upcoming": 0},
            "generated_at": datetime.utcnow().isoformat()
        }

def _user():
    return {
        "name": "Cliente",
        "plan": "ELITE",
        "status": "Activo",
        "bankroll": "10.00€",
        "telegram": "OFF",
        "roi": "Sin datos reales",
        "winrate": "Sin datos reales",
        "trust_score": 50,
        "risk": "Conservador",
        "sport": "Fútbol"
    }

def _quality(score):
    try:
        score = int(score or 0)
    except Exception:
        score = 0
    if score >= 90: return "TOP"
    if score >= 82: return "Alta"
    if score >= 74: return "Buena"
    return "Pendiente"

def _risk(score):
    try:
        score = int(score or 0)
    except Exception:
        score = 0
    if score >= 88: return "Bajo"
    if score >= 78: return "Medio"
    return "Controlado"

def _stake(score):
    try:
        score = int(score or 0)
    except Exception:
        score = 0
    if score >= 88: return "3% banca"
    if score >= 78: return "2% banca"
    return "0.5%-1%"

def card(match):
    score = match.get("shark_score") or match.get("quality_score") or 0
    return {
        "id": match.get("id"),
        "league": match.get("league") or "Competición",
        "home": match.get("home_team") or "",
        "away": match.get("away_team") or "",
        "date": match.get("date") or "SIN FECHA",
        "date_full": match.get("date_full") or "",
        "time": match.get("time") or "--:--",
        "status": match.get("status") or "PROGRAMADO",
        "relative": match.get("relative") or "",
        "market": match.get("market") or "Mercado pendiente",
        "odds": match.get("odds") or "Pendiente",
        "bookmaker": match.get("bookmaker") or "Bookmaker pendiente",
        "score": score,
        "quality": _quality(score),
        "risk": match.get("risk") or _risk(score),
        "stake": match.get("stake") or _stake(score),
        "ev": match.get("ev") or "Pendiente",
        "source": match.get("source") or "real",
        "detail_url": f"/analisis-pro/{match.get('id')}",
        "is_live": str(match.get("status","")).upper() in {"LIVE","IN_PLAY","EN DIRECTO"}
    }

def build_vm(force=False):
    feed = _get_feed(force=force)
    matches = [card(m) for m in feed.get("matches", [])]
    live = [card(m) for m in feed.get("buckets", {}).get("live", [])]
    today = [card(m) for m in feed.get("buckets", {}).get("today", [])]
    upcoming = [card(m) for m in feed.get("buckets", {}).get("upcoming", [])]
    recommended = sorted(matches, key=lambda x: int(x.get("score") or 0), reverse=True)[:10]
    return {
        "version": "V94",
        "user": _user(),
        "feed": feed,
        "counts": feed.get("counts", {"total": 0, "live": 0, "today": 0, "upcoming": 0}),
        "matches": matches,
        "recommended": recommended,
        "live": live,
        "today": today,
        "upcoming": upcoming,
        "health": {
            "ok": feed.get("ok", False),
            "source": feed.get("source", "none"),
            "message": feed.get("message"),
            "error": feed.get("error"),
            "real_core_only": True,
            "no_fake": True
        }
    }


def _score_int(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0

def build_match_analysis(match):
    """Construye lectura SHARK sin inventar datos: solo interpreta campos reales disponibles."""
    c = card(match)
    score = _score_int(c.get("score"))
    odds = match.get("odds") or c.get("odds")
    try:
        odds_f = float(odds)
    except Exception:
        odds_f = None

    positives = []
    cautions = []

    if score >= 88:
        positives.append("Señal fuerte por validación del Real Core y calidad alta del mercado.")
    elif score >= 78:
        positives.append("Señal interesante, pero necesita stake controlado.")
    elif score > 0:
        cautions.append("SHARK score moderado: no forzar entrada si la cuota se mueve en contra.")
    else:
        cautions.append("Todavía no hay score suficiente para recomendar entrada premium.")

    if odds_f is None:
        cautions.append("Cuota pendiente o no disponible: no entrar hasta que exista cuota real.")
    elif odds_f < 1.35:
        cautions.append("Cuota baja: posible poco valor si no hay ventaja clara.")
    elif odds_f > 3.5:
        cautions.append("Cuota alta: mayor varianza, stake reducido obligatorio.")
    else:
        positives.append("Rango de cuota utilizable para gestión de banca responsable.")

    if str(c.get("status", "")).upper() in {"EN DIRECTO", "LIVE", "IN_PLAY"}:
        positives.append("Contexto live detectado: revisar momentum antes de confirmar.")
        cautions.append("En directo las cuotas cambian rápido; confirmar precio antes de entrar.")
    else:
        positives.append("Partido programado: permite analizar sin presión de movimiento live.")

    why_enter = positives or ["Entrada solo si el mercado mantiene cuota real y el score no baja."]
    why_not = cautions or ["No hay alertas graves, pero la gestión de banca sigue siendo obligatoria."]

    if score >= 88 and (odds_f is None or odds_f <= 3.5):
        verdict = "ENTRADA PRO"
        action = "Apta para seguimiento premium con stake recomendado."
    elif score >= 78:
        verdict = "ENTRADA CONTROLADA"
        action = "Solo con stake moderado y cuota confirmada."
    else:
        verdict = "ESPERAR"
        action = "Mejor esperar confirmación de mercado, cuota o momentum."

    return {
        "card": c,
        "raw": match,
        "score": score,
        "verdict": verdict,
        "action": action,
        "why_enter": why_enter,
        "why_not": why_not,
        "momentum": "Live / cerca" if c.get("is_live") else "Prepartido",
        "reading": f"SHARK detecta {c.get('quality')} calidad, riesgo {c.get('risk')} y stake {c.get('stake')} para {c.get('home')} vs {c.get('away')}.",
        "data_warning": "Lectura basada en datos reales disponibles. Si falta cuota/EV, no se inventa.",
    }
