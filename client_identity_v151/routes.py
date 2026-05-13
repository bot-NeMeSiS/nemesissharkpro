
from flask import Blueprint, jsonify, render_template, session
from client_identity_v151.core import build_client_identity

client_identity_v151_bp = Blueprint("client_identity_v151", __name__)

@client_identity_v151_bp.route("/api/v151/client/identity")
def api_identity():
    return jsonify(build_client_identity(session))

@client_identity_v151_bp.route("/cliente/pro")
@client_identity_v151_bp.route("/cliente/premium")
@client_identity_v151_bp.route("/cliente/dashboard-pro")
def client_pro_page():
    return render_template("client_identity_pro_v151.html", client=build_client_identity(session))
