from flask import Blueprint, jsonify, request
from app.controllers.usercontroller import UserController

user_bp = Blueprint("users", __name__)
controller = UserController()


def response_handler(result):
    status_code = result.get("code", 200)
    return jsonify(result), status_code


@user_bp.route("/users", methods=["GET"])
def listar_users():
    result = controller.get_users()
    return response_handler(result)

@user_bp.route("/save-participants", methods=["POST"])
def create_participant():
    data = request.get_json(silent=True) or {}
    return response_handler(controller.create_participant(data))

@user_bp.route("/participants/<string:external_id>", methods=["PUT"])
def update_participant(external_id):
    """Actualiza los datos de un participante y su responsable (si tiene)"""
    data = request.get_json(silent=True) or {}
    return response_handler(controller.update_participant(external_id, data))
