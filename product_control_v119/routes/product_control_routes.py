
from flask import Blueprint, jsonify, render_template
from product_control_v119.core.product_state import build_product_state

product_control_v119_bp = Blueprint("product_control_v119", __name__)

@product_control_v119_bp.route("/api/v119/product/state")
def product_state_api():
    return jsonify(build_product_state())

@product_control_v119_bp.route("/admin/product-control")
@product_control_v119_bp.route("/admin/control-total")
@product_control_v119_bp.route("/product-control")
def product_control_page():
    return render_template("product_control_v119.html", state=build_product_state())
