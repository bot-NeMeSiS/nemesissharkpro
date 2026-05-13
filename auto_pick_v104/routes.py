
from flask import Blueprint, jsonify, request, render_template

from auto_pick_v104.engine import scan_auto_picks, normalize_candidate, explain_candidate

auto_pick_v104_bp = Blueprint("auto_pick_v104", __name__)

@auto_pick_v104_bp.route("/api/v104/auto-pick/health")
def health():
    return jsonify({
        "ok": True,
        "version": "V104",
        "module": "AUTO_PICK_ENGINE",
        "status": "ready"
    })

@auto_pick_v104_bp.route("/api/v104/auto-pick/scan", methods=["POST"])
def scan():
    payload = request.get_json(silent=True) or {}
    matches = payload.get("matches") or []
    min_score = payload.get("min_score", 68)
    max_results = payload.get("max_results", 20)
    include_rejected = bool(payload.get("include_rejected", False))
    return jsonify(scan_auto_picks(matches, min_score=min_score, max_results=max_results, include_rejected=include_rejected))

@auto_pick_v104_bp.route("/api/v104/auto-pick/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    match = payload.get("match") or payload
    candidate = normalize_candidate(match)
    return jsonify({
        "candidate": candidate,
        "explanation": explain_candidate(candidate)
    })

@auto_pick_v104_bp.route("/auto-pick-engine")
def auto_pick_page():
    return render_template("auto_pick_v104.html")
