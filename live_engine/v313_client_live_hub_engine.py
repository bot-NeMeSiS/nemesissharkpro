from datetime import datetime, timezone


def build_client_live_hub_v313(v312_payload):
    """Capa cliente sobre V312: convierte momentum en experiencia Smart Home/Match Center.
    No llama APIs externas. Solo trabaja con datos cacheados/snapshots ya disponibles.
    """
    matches = list((v312_payload or {}).get("matches") or [])
    summary = dict((v312_payload or {}).get("summary") or {})
    matches.sort(key=lambda x: (x.get("trigger") != "HOT", -int(x.get("momentum") or 0)))

    focus = _build_focus(matches)
    actions = _build_actions(matches, summary)
    home_cards = _build_home_cards(matches, summary)
    match_center = [_match_center_card(m) for m in matches[:8]]
    data_state = _data_state(matches, summary)

    return {
        "ok": True,
        "version": "V313",
        "mode": "client-live-hub-cache-first",
        "touches_api": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": _headline(matches, summary),
        "summary": summary,
        "focus": focus,
        "actions": actions,
        "home_cards": home_cards,
        "match_center": match_center,
        "data_state": data_state,
        "source_version": (v312_payload or {}).get("version", "V312"),
    }


def _headline(matches, summary):
    if not matches:
        return "Smart Live Hub preparado: esperando partidos reales cacheados."
    hot = [m for m in matches if m.get("trigger") == "HOT"]
    value = [m for m in matches if m.get("trigger") == "VALUE"]
    if hot:
        return f"{len(hot)} foco(s) HOT: el cliente debe mirar aquí primero."
    if value:
        return f"{len(value)} oportunidad(es) VALUE: revisar cuota, contexto y stake responsable."
    return summary.get("headline") or "Seguimiento live inteligente activo."


def _build_focus(matches):
    if not matches:
        return {
            "label": "SIN FOCO ACTIVO",
            "title": "No hay partidos reales cacheados ahora mismo",
            "subtitle": "La experiencia queda preparada sin consumir API.",
            "momentum": 0,
            "action": "Actualizar partidos desde las pantallas reales cuando quieras cargar datos.",
        }
    m = matches[0]
    return {
        "label": m.get("trigger", "WATCH"),
        "title": m.get("title") or "Partido destacado",
        "subtitle": f"{m.get('league') or 'Liga'} · {m.get('live_status') or 'PROGRAMADO'}",
        "momentum": int(m.get("momentum") or 0),
        "action": m.get("client_action") or "Abrir Match Center y seguir señales.",
    }


def _build_actions(matches, summary):
    if not matches:
        return [
            {"type": "DATA", "title": "Cargar contexto real", "text": "Sin datos cacheados todavía. El sistema no fuerza llamadas API desde aquí."},
            {"type": "HOME", "title": "Mantener continuidad", "text": "Smart Home puede mostrar estado seguro aunque no haya live."},
            {"type": "ML", "title": "Preparado para snapshots", "text": "Cuando entren partidos, V312/V313 ya generan señales para histórico."},
        ]
    actions = []
    hot = [m for m in matches if m.get("trigger") == "HOT"]
    low = [m for m in matches if m.get("data_health") == "LOW DATA"]
    if hot:
        actions.append({"type": "HOT", "title": "Prioridad máxima", "text": "Abrir el primer foco HOT y vigilar marcador/cuota antes de decidir."})
    if any(m.get("trigger") == "VALUE" for m in matches):
        actions.append({"type": "VALUE", "title": "Revisar valor", "text": "Comparar pick, cuota, EV y stake responsable antes de actuar."})
    if low:
        actions.append({"type": "DATA", "title": "Filtrar baja señal", "text": f"{len(low)} partido(s) necesitan más datos antes de recomendar acción."})
    actions.append({"type": "LOOP", "title": "Continuar sesión", "text": "El cliente siempre sabe qué mirar ahora, qué esperar y qué ignorar."})
    return actions[:4]


def _build_home_cards(matches, summary):
    return [
        {"label": "Momentum medio", "value": f"{int(summary.get('momentum_avg') or 0)}/99", "hint": "Pulso general del live"},
        {"label": "HOT", "value": str(summary.get("hot_count", 0)), "hint": "Prioridad máxima"},
        {"label": "WATCH", "value": str(summary.get("watch_count", 0)), "hint": "Partidos a seguir"},
        {"label": "Salud datos", "value": summary.get("data_health") or "LOW DATA", "hint": "Fiabilidad actual"},
    ]


def _match_center_card(m):
    momentum = int(m.get("momentum") or 0)
    if m.get("data_health") == "LOW DATA":
        decision = "Esperar"
    elif m.get("trigger") == "HOT":
        decision = "Seguir ahora"
    elif m.get("trigger") == "VALUE":
        decision = "Revisar valor"
    else:
        decision = "Observar"
    return {
        "id": m.get("id"),
        "title": m.get("title") or "Partido",
        "league": m.get("league") or "Liga",
        "status": m.get("live_status") or "PROGRAMADO",
        "scoreline": m.get("live_score") or "",
        "minute": m.get("live_minute") or "",
        "pick": m.get("pick") or "",
        "odds": m.get("cuota") or "",
        "trigger": m.get("trigger") or "WATCH",
        "momentum": momentum,
        "decision": decision,
        "why": m.get("trigger_reason") or "Señal generada por motor live.",
        "action": m.get("client_action") or "Guardar en seguimiento.",
        "health": m.get("data_health") or "WATCH",
    }


def _data_state(matches, summary):
    if not matches:
        return {"level": "LOW DATA", "text": "No hay partidos reales cacheados. No se rompe la pantalla ni se gasta API."}
    low = len([m for m in matches if m.get("data_health") == "LOW DATA"])
    if low == 0:
        return {"level": "OK", "text": "Datos suficientes para una experiencia cliente fluida."}
    return {"level": "WATCH", "text": f"Hay {low} partido(s) con baja señal. El motor los marca para no confundir al cliente."}
