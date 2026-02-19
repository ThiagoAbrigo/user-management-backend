from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import AuthController
from app import db
from sqlalchemy import text

auth_bp = Blueprint("auth", __name__)
controller = AuthController()

def response_handler(result):
    status_code = result.get("code", 200)
    return jsonify(result), status_code

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    return response_handler(controller.login(data))


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    return response_handler(controller.refresh())


@auth_bp.route("/health/db", methods=["GET"])
def db_health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"db": "ok"}), 200
    except Exception:
        return jsonify({"db": "error"}), 500