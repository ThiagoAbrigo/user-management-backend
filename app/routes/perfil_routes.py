from flask import Blueprint, request, jsonify
from app import db
from sqlalchemy import text
from app.controllers.authcontroller import AuthController
from app.controllers.perfilcontroller import PerfilController

perfil_bp = Blueprint("perfil", __name__)
perfil_controller = PerfilController()


@perfil_bp.route("/profile", methods=["GET"])
def profile():
    external_id = request.args.get("external_id")
    return perfil_controller.get_profile(external_id)

@perfil_bp.route('/perfil/<external_id>', methods=['PUT', 'OPTIONS'])
def update_profile_route(external_id):
    # Manejo de preflight OPTIONS
    if request.method == "OPTIONS":
        return '', 200
    return perfil_controller.update_profile(external_id)