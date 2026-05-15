"""
NeMeSiS SHARK PRO · V319
Unified Experience System PRO

Capa de experiencia cliente: no llama APIs externas. Recibe el payload de V318
/ cadena anterior y devuelve un sistema de navegación, diseño, acciones y estados
unificado para que la app se sienta menos como pantallas sueltas y más como OS.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List


def _safe_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    return []


def _pick_matches(v318_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("visual_matches", "matches", "focus_matches", "watchlist"):
        rows = _safe_list(v318_payload.get(key))
        if rows:
            return rows[:8]
    modules = _safe_list(v318_payload.get("modules"))
    out = []
    for m in modules:
        for key in ("matches", "items", "cards"):
            out.extend(_safe_list(m.get(key)))
    return out[:8]


def _score_activity(match: Dict[str, Any]) -> int:
    raw = " ".join(str(match.get(k, "")) for k in ("status", "state", "tag", "level", "signal", "mood")).upper()
    score = 45
    if "HOT" in raw: score += 30
    if "WATCH" in raw: score += 18
    if "VALUE" in raw or "EDGE" in raw: score += 14
    if "LIVE" in raw: score += 10
    if "LOW" in raw: score -= 12
    return max(0, min(100, score))


def build_unified_experience_system_v319(v318_payload: Dict[str, Any]) -> Dict[str, Any]:
    matches = _pick_matches(v318_payload or {})
    visual_summary = v318_payload.get("visual_summary") if isinstance(v318_payload.get("visual_summary"), dict) else {}
    hot_count = int(visual_summary.get("hot") or 0)
    watch_count = int(visual_summary.get("watch") or 0)
    energy = int(visual_summary.get("energy") or 0)

    experience_cards = []
    for idx, m in enumerate(matches[:6], start=1):
        teams = m.get("teams") or m.get("title") or m.get("match") or m.get("name") or "Partido monitorizado"
        if isinstance(teams, list):
            teams = " vs ".join(map(str, teams[:2]))
        activity = _score_activity(m)
        status = str(m.get("status") or m.get("state") or m.get("signal") or ("HOT" if activity >= 75 else "WATCH" if activity >= 55 else "SEGUIMIENTO"))
        experience_cards.append({
            "rank": idx,
            "title": str(teams),
            "status": status,
            "activity": activity,
            "headline": "Zona caliente" if activity >= 75 else "Vigilar evolución" if activity >= 55 else "Contexto guardado",
            "action": "Abrir Match Center" if activity >= 55 else "Guardar seguimiento",
            "href": "/cliente/match-center-premium",
            "reason": "Unificado con Live Visual, Continuity y Match Center para reducir saltos entre pantallas."
        })

    if not experience_cards:
        experience_cards = [
            {"rank": 1, "title": "Tu app está lista", "status": "SAFE", "activity": 42, "headline": "Modo seguro activo", "action": "Abrir Mi día", "href": "/cliente/experiencia", "reason": "No hay datos cacheados ahora mismo, pero la experiencia carga sin consumir API."},
            {"rank": 2, "title": "Live Focus", "status": "WATCH", "activity": 58, "headline": "Preparado para directo", "action": "Ir a Live Focus", "href": "/cliente/smart-live-hub", "reason": "Cuando existan partidos cacheados se ordenarán por prioridad visual."},
        ]

    sections = [
        {"id": "home", "label": "Mi día", "href": "/cliente/experiencia", "role": "inicio", "priority": 1},
        {"id": "live", "label": "Live", "href": "/cliente/live-visual", "role": "emoción", "priority": 2},
        {"id": "focus", "label": "Focus", "href": "/cliente/smart-live-hub", "role": "decisión", "priority": 3},
        {"id": "center", "label": "Match Center", "href": "/cliente/match-center-premium", "role": "partido", "priority": 4},
        {"id": "memory", "label": "Memoria", "href": "/cliente/shark-memory", "role": "histórico", "priority": 5},
        {"id": "account", "label": "Cuenta", "href": "/cliente/dashboard", "role": "usuario", "priority": 6},
    ]

    next_actions = []
    if hot_count:
        next_actions.append({"type": "hot", "label": "Revisar zonas HOT", "href": "/cliente/live-visual", "urgency": "alta"})
    if watch_count:
        next_actions.append({"type": "watch", "label": "Abrir partidos vigilados", "href": "/cliente/smart-live-hub", "urgency": "media"})
    next_actions.extend([
        {"type": "continue", "label": "Continuar mi sesión", "href": "/cliente/continuity-center", "urgency": "media"},
        {"type": "center", "label": "Entrar en Match Center", "href": "/cliente/match-center-premium", "urgency": "normal"},
    ])

    return {
        "ok": True,
        "version": "V319",
        "name": "Unified Experience System PRO",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "headline": "Tu experiencia NeMeSiS está unificada: menos pantallas sueltas, más app premium.",
        "subheadline": "Mi día, Live, Focus, Match Center, Memoria y Cuenta trabajan como un solo recorrido.",
        "experience_score": max(78, min(99, 84 + (hot_count * 2) + (watch_count) + int(energy/20))),
        "mood": "PREMIUM APP FEEL",
        "design_tokens": {
            "radius": "22px",
            "spacing": "16/20/28",
            "surface": "glass-dark",
            "motion": "soft-live",
            "density": "mobile-first",
            "identity": "blue-neon-gold"
        },
        "sections": sections,
        "experience_cards": experience_cards,
        "next_actions": next_actions[:5],
        "client_rules": [
            "Una sola barra superior coherente.",
            "Cards con el mismo lenguaje visual.",
            "Acciones claras: mirar, seguir, decidir o volver a cuenta.",
            "Nada de pantallas aisladas sin salida.",
            "Abrir esta vista no consume cuota de API."
        ],
        "bridge": {
            "from": "V318 Live Visual System",
            "to": "V319 Unified Experience System",
            "next": "V320 Client Flow Engine / Timeline Real"
        },
        "raw_v318_summary": visual_summary,
    }
