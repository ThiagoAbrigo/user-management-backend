from flask import Blueprint, jsonify, request
from app.controllers.usercontroller import UserController
from app.controllers.rolecontroller import RolController

user_bp = Blueprint("users", __name__)
controller = UserController()
rolecontrolle = RolController()

@user_bp.route("/users", methods=["GET"])
def listar_users():
    result = controller.listar_usuarios()
    return result

@user_bp.route("/save-user", methods=["POST"])
def create_users():
    return controller.registrar_usuario()

@user_bp.route("/role", methods=["GET"])
def listar_roles():
    result = rolecontrolle.listar_roles()
    return result