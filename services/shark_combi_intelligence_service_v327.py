# -*- coding: utf-8 -*-
"""V327 · SHARK COMBI INTELLIGENCE PRO

Capa inteligente para combinadas 1X2.
- NO llama APIs externas.
- Usa el constructor V326 y mejora ranking, explicación y modos.
- Nunca inventa partidos si no hay datos reales/caché suficientes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _mode_profile(mode: str) -> Dict[str, Any]:
    key = str(mode or "balanceado").strip().lower()
    if key in {"bajo", "seguro", "conservador"}:
        return {
            "key": "conservador",
            "label": "Conservador",
            "recommended_count": 5,
            "risk_note": "Prioriza estabilidad y evita cuotas demasiado altas.",
            "score_boost": 5,
        }
    if key in {"alto", "agresivo", "arriesgado"}:
        return {
            "key": "agresivo",
            "label": "Agresivo",
            "recommended_count": 9,
            "risk_note": "Busca más retorno, aceptando más riesgo global.",
            "score_boost": -3,
        }
    return {
        "key": "balanceado",
        "label": "Balanceado",
        "recommended_count": 7,
        "risk_note": "Equilibra confianza y retorno.",
        "score_boost": 0,
    }


def _confidence(selection: Dict[str, Any], profile: Dict[str, Any]) -> int:
    score = _int(selection.get("score"), 65)
    combi_score = _num(selection.get("combi_score"), score)
    odds = _num(selection.get("odds"), 1.0)
    # Penalización progresiva por cuota alta en combinadas.
    odds_penalty = max(0, int((odds - 2.20) * 8)) if odds > 2.20 else 0
    value = int((score * 0.55) + (combi_score * 0.35) + profile.get("score_boost", 0) - odds_penalty)
    return max(1, min(99, value))


def _decision(selection: Dict[str, Any], confidence: int, profile: Dict[str, Any]) -> str:
    odds = _num(selection.get("odds"), 0)
    if confidence >= 82 and odds <= 2.35:
        return "Entra fuerte para este perfil"
    if confidence >= 72:
        return "Buena candidata para combinar"
    if profile["key"] == "agresivo" and confidence >= 64:
        return "Solo para modo agresivo"
    return "Vigilar, no forzar"


def _enhance_selection(selection: Dict[str, Any], profile: Dict[str, Any], index: int) -> Dict[str, Any]:
    item = dict(selection)
    confidence = _confidence(item, profile)
    item["rank"] = index
    item["confidence"] = confidence
    item["decision"] = _decision(item, confidence, profile)
    item["intelligence_reason"] = (
        f"{item.get('result_label','1X2')} · confianza {confidence}/100 · "
        f"cuota {item.get('odds')} · perfil {profile['label'].lower()}."
    )
    item["risk_control"] = (
        "Mantener stake bajo; en combinadas largas el riesgo crece aunque cada pick sea bueno."
        if index <= 12 else "Fuera del núcleo principal de la combinada."
    )
    return item


def _copy_text(payload: Dict[str, Any], profile: Dict[str, Any]) -> str:
    selected = payload.get("selections") or []
    stake = _num((payload.get("summary") or {}).get("stake"), 0.10)
    lines = [f"SHARK COMBI INTELLIGENCE 1X2 · {len(selected)} partidos · {profile['label']} · Stake {stake:.2f} €"]
    for i, s in enumerate(selected, 1):
        lines.append(f"{i}. {s.get('title','Partido')} — {s.get('result','?')} · cuota {s.get('odds')} · confianza {s.get('confidence','-')}/100")
    summary = payload.get("summary") or {}
    if selected:
        lines.append(f"Cuota total estimada: {summary.get('total_odds', 0)}")
        lines.append(f"Retorno posible: {summary.get('possible_return', 0)} €")
        lines.append("Aviso: no hay combinada perfecta garantizada; usar como filtro inteligente.")
    return "\n".join(lines)


def build_shark_combi_intelligence(count: int = 8, stake: float = 0.10, mode: str = "balanceado", day: str = "hoy") -> Dict[str, Any]:
    """Construye una combinada 1X2 inteligente encima del motor V326."""
    profile = _mode_profile(mode)
    try:
        from services.shark_combi_1x2_service_v326 import build_shark_combi_1x2
        base = build_shark_combi_1x2(count=count, stake=stake, risk=profile["key"], day=day)
    except Exception as exc:
        return {
            "ok": True,
            "version": "V327",
            "name": "SHARK COMBI INTELLIGENCE PRO",
            "touches_api": False,
            "mode": profile,
            "headline": "Combinadas inteligentes 1X2",
            "subheadline": "Modo seguro activo: no se pudieron leer datos reales guardados.",
            "data_health": {"label": "MODO SEGURO", "tone": "watch", "text": str(exc)[:180]},
            "summary": {"total_odds": 0, "stake": _num(stake, 0.10), "possible_return": 0, "possible_profit": 0, "avg_score": 0, "risk_label": "Sin datos"},
            "selections": [],
            "copy_text": "Sin combinada disponible todavía.",
            "warnings": ["Carga cuotas/partidos 1X2 y vuelve a construir la combinada.", "No se hacen llamadas API desde esta pantalla."],
        }

    selected = base.get("selections") or []
    enhanced: List[Dict[str, Any]] = []
    for idx, item in enumerate(selected, 1):
        enhanced.append(_enhance_selection(item, profile, idx))
    base["selections"] = enhanced
    base["ok"] = True
    base["version"] = "V327"
    base["name"] = "SHARK COMBI INTELLIGENCE PRO"
    base["touches_api"] = False
    base["generated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    base["mode"] = profile
    base["headline"] = "SHARK Combi Intelligence 1X2"
    base["subheadline"] = "Elige las mejores selecciones 1/X/2 del día usando datos ya guardados, filtros de riesgo y confianza SHARK."
    base["copy_text"] = _copy_text(base, profile)
    base["intelligence"] = {
        "recommended_count": profile["recommended_count"],
        "risk_note": profile["risk_note"],
        "quality_gate": "No rellena con picks basura: si faltan datos, deja la combinada incompleta.",
        "api_policy": "No gasta API extra al abrir; reutiliza picks/cuotas/cache existentes.",
    }
    base["actions"] = [
        {"label": "Copiar combinada", "type": "copy"},
        {"label": "Conservador", "href": "/cliente/combi-inteligente?modo=conservador&partidos=5&stake=0.10"},
        {"label": "Balanceado", "href": "/cliente/combi-inteligente?modo=balanceado&partidos=7&stake=0.10"},
        {"label": "Agresivo", "href": "/cliente/combi-inteligente?modo=agresivo&partidos=9&stake=0.10"},
    ]
    warnings = list(base.get("warnings") or [])
    warnings.append("No existe una combinada perfecta garantizada: esto filtra y ordena, no promete aciertos.")
    base["warnings"] = warnings
    return base
