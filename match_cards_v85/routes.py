
from flask import Blueprint, jsonify, render_template
from .match_cards_engine import get_v85_status, demo_cards

match_cards_v85_bp = Blueprint("match_cards_v85", __name__)

@match_cards_v85_bp.route("/admin/match-cards-pro")
def admin_match_cards_pro():
    return render_template("admin_match_cards_v85.html", status=get_v85_status())

@match_cards_v85_bp.route("/match-cards-pro")
def match_cards_pro():
    return render_template("match_cards_v85.html", cards=demo_cards())

@match_cards_v85_bp.route("/api/match-cards-pro/status")
def api_match_cards_status():
    return jsonify(get_v85_status())
