from flask import Blueprint, jsonify, request
from app.utils.jwt_required import jwt_required, get_jwt_identity
from app.controllers.usercontroller import UserController

user_bp = Blueprint("users", __name__)
controller = UserController()


def response_handler(result):
    print("TYPE:", type(result), result)
    status_code = result.get("code", 200)
    return jsonify(result), status_code


@user_bp.route("/users", methods=["GET"])
@jwt_required
def listar_users():
    result = controller.get_users()
    return response_handler(result)


@user_bp.route("/users/<string:external_id>/status", methods=["PUT"])
@jwt_required
def cambiar_estado(external_id):
    data = request.json
    new_status = data.get("status") if data else None
    return response_handler(controller.change_status(external_id, new_status))


@user_bp.route("/users/search-java", methods=["POST"])
@jwt_required
def buscar_usuario_java():
    """Busca usuario exclusivamente en el microservicio Java."""
    data = request.json
    dni = data.get("dni")

    if not dni:
        return jsonify({"status": "error", "msg": "Falta el DNI", "code": 400}), 400

    return response_handler(controller.search_in_java(dni))


@user_bp.route("/save-participants", methods=["POST"])
# @jwt_required
def create_participant():
    data = request.get_json(silent=True) or {}
    return response_handler(controller.create_participant(data))


@user_bp.route("/save-user", methods=["POST"])
@jwt_required
def create_user():
    """
    Registra un usuario del sistema (Docente o Pasante)
    """
    data = request.get_json(silent=True) or {}

    return response_handler(controller.create_user(data))


@user_bp.route("/users/profile", methods=["GET"])
@jwt_required
def get_user_profile():
    """Obtiene el perfil del usuario autenticado."""
    try:
        current_user_id = get_jwt_identity()

        if not current_user_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "msg": "No se pudo identificar al usuario",
                        "code": 401,
                    }
                ),
                401,
            )

        result = controller.get_profile(current_user_id)
        return response_handler(result)

    except Exception as e:
        print(f"[ERROR] get_user_profile: {str(e)}")
        return jsonify({"status": "error", "msg": f"Error: {str(e)}", "code": 500}), 500


@user_bp.route("/users/profile", methods=["PUT"])
@jwt_required
def update_user_profile():
    """Actualiza el perfil del usuario autenticado."""
    try:
        current_user_id = get_jwt_identity()

        if not current_user_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "msg": "No se pudo identificar al usuario",
                        "code": 401,
                    }
                ),
                401,
            )

        token = request.headers.get("Authorization")

        data = request.get_json(silent=True) or {}

        print(f"[DEBUG] Actualizando perfil para user_id: {current_user_id}")
        print(f"[DEBUG] Datos recibidos: {data}")

        result = controller.update_profile(current_user_id, data, token)

        print(f"[DEBUG] Resultado del servicio: {result}")

        return response_handler(result)
    except Exception as e:
        print(f"[ERROR] update_user_profile: {str(e)}")
        return jsonify({"status": "error", "msg": f"Error: {str(e)}", "code": 500}), 500


@user_bp.route("/participants/<string:external_id>", methods=["GET"])
def get_participant(external_id):
    """Obtiene un participante por su external_id con su responsable (si tiene)"""
    return response_handler(controller.get_participant_by_id(external_id))


@user_bp.route("/participants/active/count", methods=["GET"])
@jwt_required
def get_active_participants_count():
    return response_handler(controller.get_active_participants_count())


@user_bp.route("/participants/<string:external_id>", methods=["PUT"])
@jwt_required
def update_participant(external_id):
    """Actualiza los datos de un participante y su responsable (si tiene)"""
    data = request.get_json(silent=True) or {}
    return response_handler(controller.update_participant(external_id, data))
