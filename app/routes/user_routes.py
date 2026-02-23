from flask import Blueprint, jsonify, request
from app.controllers.usercontroller import UserController

user_bp = Blueprint("users", __name__)
controller = UserController()


def response_handler(result):
    if isinstance(result, tuple):
        data, status_code = result
        return jsonify(data), status_code


@user_bp.route("/users", methods=["GET"])
def listar_users():
    result = controller.get_users()
    return response_handler(result)

@user_bp.route("/save-user", methods=["POST"])
def create_users():
    data = request.get_json(silent=True) or {}
    return response_handler(controller.create_user(data))

@user_bp.route("/participants/<string:external_id>", methods=["PUT"])
def update_participant(external_id):
    """Actualiza los datos de un participante y su responsable (si tiene)"""
    data = request.get_json(silent=True) or {}
    return response_handler(controller.update_participant(external_id, data))
