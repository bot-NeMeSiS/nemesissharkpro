from datetime import datetime


def _safe(value, default="Pendiente"):
    value = value if value is not None else default
    text = str(value).strip()
    return text if text else default


def _score(match):
    for key in ("shark_score", "quality_score", "score"):
        try:
            return int(float(match.get(key)))
        except Exception:
            pass
    return 0


def _odds(match):
    try:
        return float(match.get("odds"))
    except Exception:
        return None


def entry_level(match):
    score = _score(match)
    risk = _safe(match.get("risk"), "Pendiente").lower()
    odds = _odds(match)
    if score >= 88 and risk in {"bajo", "medio"}:
        return "Entrada fuerte controlada"
    if score >= 78:
        return "Entrada válida con stake prudente"
    if odds and odds >= 4:
        return "Solo seguimiento: cuota alta y volatilidad elevada"
    return "Esperar confirmación"


def build_match_reading(match):
    score = _score(match)
    odds = _odds(match)
    risk = _safe(match.get("risk"))
    stake = _safe(match.get("stake"))
    selection = _safe(match.get("selection") or match.get("market"), "Mercado pendiente")
    home = _safe(match.get("home_team"), "Local")
    away = _safe(match.get("away_team"), "Visitante")
    status = _safe(match.get("status"))

    positives = []
    negatives = []

    if score >= 80:
        positives.append("calidad del feed y validación real alta")
    else:
        negatives.append("score SHARK todavía mejorable")

    if odds is not None:
        if 1.45 <= odds <= 2.4:
            positives.append("cuota dentro de rango estable")
        elif odds > 3.2:
            negatives.append("cuota alta con más varianza")
        else:
            negatives.append("cuota con margen de value limitado")
    else:
        negatives.append("sin cuota real confirmada")

    if status == "EN DIRECTO":
        positives.append("partido en zona live/cercana para seguimiento")
    elif status == "PROGRAMADO":
        positives.append("entrada prepartido con margen para confirmar mercado")

    return {
        "match_id": match.get("id"),
        "title": f"{home} vs {away}",
        "league": _safe(match.get("league"), "Competición"),
        "status": status,
        "time": _safe(match.get("time"), "--:--"),
        "date": _safe(match.get("date"), "SIN FECHA"),
        "selection": selection,
        "odds": odds,
        "bookmaker": _safe(match.get("bookmaker"), "Casa pendiente"),
        "shark_score": score,
        "risk": risk,
        "stake": stake,
        "ev": _safe(match.get("ev")),
        "entry_level": entry_level(match),
        "why_enter": positives or ["datos reales disponibles y partido validado por Real Core"],
        "why_wait": negatives or ["no hay bloqueo fuerte; mantener disciplina de stake"],
        "shark_reading": (
            f"SHARK detecta {entry_level(match).lower()} en {home} vs {away}. "
            f"La lectura combina score {score}, riesgo {risk}, stake {stake} y cuota real {odds if odds else 'pendiente'}."
        ),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def answer_question(question, feed):
    q = (question or "").strip().lower()
    matches = feed.get("matches", []) if isinstance(feed, dict) else []
    counts = feed.get("counts", {}) if isinstance(feed, dict) else {}

    if not matches:
        return {
            "answer": "Ahora mismo Real Core no tiene partidos reales válidos. No muestro demos ni invento picks.",
            "intent": "empty_real_core",
            "recommended_matches": [],
        }

    ranked = sorted(matches, key=lambda m: _score(m), reverse=True)
    top = ranked[:5]

    if any(word in q for word in ["mejor", "top", "fuerte", "entrar", "pick"]):
        best = top[0]
        reading = build_match_reading(best)
        answer = f"El pick más fuerte ahora mismo es {reading['title']} — {reading['selection']} con SHARK Score {reading['shark_score']}. Stake: {reading['stake']}."
        intent = "best_pick"
    elif any(word in q for word in ["live", "directo", "ahora"]):
        live = feed.get("buckets", {}).get("live", [])
        answer = f"Hay {len(live)} partidos live reales detectados. Te priorizo los de mayor SHARK Score." if live else "Ahora no hay partidos live reales en Real Core. Te muestro los mejores de hoy/próximos."
        top = sorted(live or matches, key=lambda m: _score(m), reverse=True)[:5]
        intent = "live_center"
    elif any(word in q for word in ["riesgo", "peligro", "no entrar"]):
        answer = "Revisión de riesgo: evita cuotas muy altas, score bajo o mercados sin cuota confirmada. Te marco los partidos con lectura más prudente."
        intent = "risk_review"
    else:
        answer = f"Real Core tiene {counts.get('total', len(matches))} partidos reales: {counts.get('live', 0)} live, {counts.get('today', 0)} hoy y {counts.get('upcoming', 0)} próximos."
        intent = "overview"

    return {
        "answer": answer,
        "intent": intent,
        "recommended_matches": [build_match_reading(m) for m in top],
        "real_core_ok": bool(feed.get("ok")),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
