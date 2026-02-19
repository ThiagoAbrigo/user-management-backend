from app.models import User
from werkzeug.security import check_password_hash
from app.utils.responses import success_response, error_response


class AuthController:
    def login(self, data):

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return error_response("Email y contraseña son obligatorios"), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return error_response("Usuario no encontrado", 404), 404

        if not check_password_hash(user.password, password):
            return error_response("Contraseña incorrecta", 401), 401

        return (
            success_response(
                "Login exitoso",
                {"id": user.id, "email": user.email, "role": user.role},
            ),
            200,
        )
