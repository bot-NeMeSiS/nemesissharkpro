# -*- coding: utf-8 -*-
"""V326 · SHARK COMBI 1X2 BUILDER PRO

Constructor seguro de combinadas 1X2.
- No llama APIs externas.
- Usa picks/cuotas/cache ya guardados en SQLite.
- Si no hay datos reales suficientes, devuelve modo seguro sin inventar partidos.
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, Iterable, List, Optional, Tuple

DB_PATH = os.environ.get("DB_PATH", "/data/database.db").strip() or "/data/database.db"


def _connect(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _float(value: Any, default: float = 0.0) -> float:
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


def _today_str() -> str:
    return date.today().isoformat()


def _safe_text(v: Any, default: str = "") -> str:
    return str(v or default).strip()


def _split_title(title: str) -> Tuple[str, str]:
    text = _safe_text(title)
    for sep in [" vs ", " VS ", " v ", " - ", "–"]:
        if sep in text:
            a, b = text.split(sep, 1)
            return a.strip(), b.strip()
    return text or "Local", "Visitante"


def _normalize_pick_to_1x2(pick: str, title: str = "") -> Optional[str]:
    """Devuelve 1, X o 2 si el pick puede mapearse claramente a mercado 1X2."""
    raw = _safe_text(pick)
    low = raw.lower()
    if not raw:
        return None
    if low in {"x", "empate", "draw", "tie"} or "empate" in low or "draw" in low:
        return "X"
    home, away = _split_title(title)
    home_low = home.lower()
    away_low = away.lower()
    # Evitar confundir mercados no 1X2
    banned = ["más de", "menos de", "over", "under", "hándicap", "handicap", "+", "corners", "tarjetas"]
    if any(b in low for b in banned):
        return None
    if home_low and home_low in low:
        return "1"
    if away_low and away_low in low:
        return "2"
    if "local" in low or low.startswith("1"):
        return "1"
    if "visitante" in low or low.startswith("2"):
        return "2"
    return None


def _result_label(result: str, title: str) -> str:
    home, away = _split_title(title)
    if result == "1":
        return f"1 · Gana {home}"
    if result == "2":
        return f"2 · Gana {away}"
    return "X · Empate"


def _risk_profile(risk: str) -> Dict[str, Any]:
    r = _safe_text(risk, "equilibrado").lower()
    if r in {"bajo", "conservador", "seguro"}:
        return {"key": "conservador", "min_odds": 1.20, "max_odds": 2.25, "max_avg_odds": 1.85, "min_score": 72, "label": "Conservador"}
    if r in {"alto", "agresivo", "arriesgado"}:
        return {"key": "agresivo", "min_odds": 1.35, "max_odds": 3.80, "max_avg_odds": 2.70, "min_score": 62, "label": "Agresivo"}
    return {"key": "equilibrado", "min_odds": 1.25, "max_odds": 2.85, "max_avg_odds": 2.20, "min_score": 68, "label": "Equilibrado"}


def _candidate_score(row: Dict[str, Any], profile: Dict[str, Any]) -> float:
    odds = _float(row.get("odds"), 0)
    shark = _int(row.get("score"), 65)
    ev = _float(row.get("ev"), 0)
    if odds <= 1:
        return 0
    # Punto dulce para combinadas: cuotas útiles pero no absurdas.
    sweet = 1.70 if profile["key"] == "conservador" else 2.05 if profile["key"] == "equilibrado" else 2.45
    distance_penalty = abs(odds - sweet) * 7.5
    odds_bonus = min(16, odds * 4)
    ev_bonus = min(12, max(0, ev) * 1.2)
    return round(max(0, shark + odds_bonus + ev_bonus - distance_penalty), 2)


def _read_picks_from_db(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    rows: List[Dict[str, Any]] = []
    try:
        conn = _connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT title, pick, league, sport, cuota, odds_decimal, odds_bookmaker, odds_market,
                   kickoff_time, commence_time, score, ev, source, active
            FROM picks
            WHERE COALESCE(active,1)=1
              AND LOWER(COALESCE(odds_market,''))='h2h'
            ORDER BY CAST(COALESCE(score,0) AS INTEGER) DESC
            LIMIT 250
        """)
        for r in cur.fetchall():
            d = dict(r)
            odds = _float(d.get("odds_decimal") or d.get("cuota"), 0)
            result = _normalize_pick_to_1x2(d.get("pick"), d.get("title"))
            if result and odds > 1:
                rows.append({
                    "title": _safe_text(d.get("title"), "Partido"),
                    "league": _safe_text(d.get("league") or d.get("sport"), "Fútbol"),
                    "pick": _safe_text(d.get("pick")),
                    "result": result,
                    "result_label": _result_label(result, d.get("title")),
                    "odds": odds,
                    "bookmaker": _safe_text(d.get("odds_bookmaker"), "Casa disponible"),
                    "kickoff_time": _safe_text(d.get("kickoff_time") or d.get("commence_time")),
                    "score": _int(d.get("score"), 65),
                    "ev": _float(d.get("ev"), 0),
                    "source": _safe_text(d.get("source"), "picks_db"),
                })
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
    return rows


def _read_cached_auto_engine(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    out: List[Dict[str, Any]] = []
    try:
        conn = _connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT payload FROM api_cache WHERE cache_key LIKE '%shark_auto_engine%' ORDER BY created_at DESC LIMIT 3")
        for row in cur.fetchall():
            try:
                payload = json.loads(row["payload"] or "{}")
            except Exception:
                payload = {}
            for p in payload.get("picks") or []:
                if str(p.get("market") or p.get("odds_market") or "").lower() != "h2h":
                    continue
                title = _safe_text(p.get("title"), "Partido")
                result = _normalize_pick_to_1x2(p.get("pick"), title)
                odds = _float(p.get("cuota") or p.get("odds_decimal"), 0)
                if result and odds > 1:
                    out.append({
                        "title": title,
                        "league": _safe_text(p.get("league") or p.get("sport"), "Fútbol"),
                        "pick": _safe_text(p.get("pick")),
                        "result": result,
                        "result_label": _result_label(result, title),
                        "odds": odds,
                        "bookmaker": _safe_text(p.get("bookmaker") or p.get("odds_bookmaker"), "Casa disponible"),
                        "kickoff_time": _safe_text(p.get("commence_time") or p.get("kickoff_time")),
                        "score": _int(p.get("score"), 65),
                        "ev": _float(p.get("ev"), 0),
                        "source": "api_cache",
                    })
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
    return out


def _dedupe(candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for c in candidates:
        key = (_safe_text(c.get("title")).lower(), _safe_text(c.get("result")))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def build_shark_combi_1x2(count: int = 8, stake: float = 0.10, risk: str = "equilibrado", day: str = "hoy", db_path: str = DB_PATH) -> Dict[str, Any]:
    count = max(2, min(20, _int(count, 8)))
    stake = max(0.01, min(1000.0, _float(stake, 0.10)))
    profile = _risk_profile(risk)

    raw_candidates = _dedupe(_read_picks_from_db(db_path) + _read_cached_auto_engine(db_path))
    candidates: List[Dict[str, Any]] = []
    for c in raw_candidates:
        odds = _float(c.get("odds"), 0)
        score = _int(c.get("score"), 65)
        if odds < profile["min_odds"] or odds > profile["max_odds"]:
            continue
        if score < profile["min_score"]:
            continue
        c["combi_score"] = _candidate_score(c, profile)
        c["why"] = _why_candidate(c, profile)
        c["why_not"] = _why_not_candidate(c, profile)
        candidates.append(c)

    candidates = sorted(candidates, key=lambda x: (x.get("combi_score", 0), x.get("score", 0)), reverse=True)
    selected = candidates[:count]
    total_odds = 1.0
    for s in selected:
        total_odds *= _float(s.get("odds"), 1.0)
    total_odds = round(total_odds, 2) if selected else 0.0
    possible_return = round(stake * total_odds, 2) if total_odds else 0.0
    possible_profit = round(possible_return - stake, 2) if possible_return else 0.0
    avg_score = round(sum(_int(s.get("score"), 0) for s in selected) / len(selected), 1) if selected else 0
    risk_label = _overall_risk(len(selected), total_odds, profile)

    copy_lines = [f"SHARK COMBI 1X2 · {len(selected)} partidos · Stake {stake:.2f} €"]
    for i, s in enumerate(selected, 1):
        copy_lines.append(f"{i}. {s['title']} — {s['result']} ({s['result_label']}) · cuota {s['odds']}")
    if selected:
        copy_lines.append(f"Cuota total estimada: {total_odds}")
        copy_lines.append(f"Retorno posible: {possible_return:.2f} €")

    return {
        "ok": True,
        "version": "V326",
        "name": "SHARK COMBI 1X2 BUILDER PRO",
        "touches_api": False,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "params": {"count_requested": count, "stake": stake, "risk": profile["label"], "day": day},
        "headline": "Constructor de combinadas 1X2",
        "subheadline": "Busca las mejores selecciones 1/X/2 usando datos y cuotas ya guardadas. No garantiza aciertos; ayuda a filtrar mejor.",
        "data_health": _data_health(len(raw_candidates), len(selected), count),
        "available_candidates": len(raw_candidates),
        "filtered_candidates": len(candidates),
        "selected_count": len(selected),
        "selections": selected,
        "summary": {
            "total_odds": total_odds,
            "stake": stake,
            "possible_return": possible_return,
            "possible_profit": possible_profit,
            "avg_score": avg_score,
            "risk_label": risk_label,
        },
        "copy_text": "\n".join(copy_lines),
        "warnings": _warnings(len(selected), count, total_odds),
        "actions": [
            {"label": "Copiar combinada", "type": "copy"},
            {"label": "Bajar riesgo", "href": "/cliente/combi-1x2?riesgo=conservador&partidos=5&stake=0.10"},
            {"label": "Modo agresivo", "href": "/cliente/combi-1x2?riesgo=agresivo&partidos=9&stake=0.10"},
        ],
    }


def _why_candidate(c: Dict[str, Any], profile: Dict[str, Any]) -> str:
    odds = _float(c.get("odds"), 0)
    score = _int(c.get("score"), 0)
    ev = _float(c.get("ev"), 0)
    parts = [f"Mercado 1X2 limpio", f"SHARK score {score}/100", f"cuota {odds}"]
    if ev > 0:
        parts.append(f"valor detectado +{ev:.1f}%")
    parts.append(f"encaja con perfil {profile['label'].lower()}")
    return " · ".join(parts) + "."


def _why_not_candidate(c: Dict[str, Any], profile: Dict[str, Any]) -> str:
    odds = _float(c.get("odds"), 0)
    if odds >= 2.8:
        return "Cuota alta: puede subir mucho el retorno, pero también el riesgo de romper la combinada."
    if odds <= 1.35:
        return "Cuota baja: aporta estabilidad, pero aumenta poco el retorno total."
    return "En combinadas largas, incluso selecciones buenas pueden fallar; mantener stake bajo es lo correcto."


def _overall_risk(n: int, total_odds: float, profile: Dict[str, Any]) -> str:
    if n >= 10 or total_odds >= 80:
        return "Alto por número de partidos"
    if n >= 7 or total_odds >= 25:
        return "Medio/alto controlado"
    if profile["key"] == "conservador" and n <= 5:
        return "Conservador"
    return profile["label"]


def _data_health(raw: int, selected: int, requested: int) -> Dict[str, str]:
    if selected >= requested:
        return {"label": "BUENA", "tone": "safe", "text": "Hay suficientes selecciones 1X2 para construir la combinada solicitada."}
    if selected > 0:
        return {"label": "MEDIA", "tone": "watch", "text": "Hay selecciones reales, pero no suficientes para completar el número pedido con filtros estrictos."}
    if raw > 0:
        return {"label": "BAJA", "tone": "risk", "text": "Hay datos guardados, pero no cumplen filtros 1X2/riesgo para esta combinada."}
    return {"label": "SIN DATOS", "tone": "risk", "text": "No hay picks/cuotas 1X2 guardados todavía. Carga partidos/cuotas primero para construir la combinada."}


def _warnings(selected: int, requested: int, total_odds: float) -> List[str]:
    warnings = [
        "No existe una combinada perfecta garantizada: úsalo como filtro inteligente, no como promesa de acierto.",
        "Para 9-12 partidos, stake bajo como 0,10 € tiene sentido porque el riesgo global sube mucho.",
    ]
    if selected < requested:
        warnings.append("No se completó el número solicitado porque el sistema prefirió no rellenar con selecciones débiles.")
    if total_odds >= 100:
        warnings.append("Cuota total muy alta: retorno atractivo, pero probabilidad real más baja.")
    return warnings
