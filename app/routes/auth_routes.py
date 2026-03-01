from flask import Blueprint, request, jsonify
from app import db
from sqlalchemy import text
from app.controllers.authcontroller import AuthController
from app.controllers.perfilcontroller import PerfilController

auth_bp = Blueprint("auth", __name__)
controller = AuthController()
perfil_controller = PerfilController()

def response_handler(result):
    if isinstance(result, tuple):
        data, status_code = result
        return jsonify(data), status_code

    return jsonify(result), 200
    
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    return controller.login(data)

@auth_bp.route("/profile", methods=["GET"])
def profile():
    external_id = request.args.get("external_id")
    return perfil_controller.get_profile(external_id)

@auth_bp.route("/health/db", methods=["GET"])
def db_health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"db": "ok"}), 200
    except Exception:
        return jsonify({"db": "error"}), 500