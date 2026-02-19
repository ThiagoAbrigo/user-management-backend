import requests
from app.config.config import Config
from app.utils.responses import error_response
from app.utils.jwt import generate_token
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db


class AuthService:
    def login(self, data):
        email, password = self._get_credentials(data)

        if not email or not password:
            return error_response("Ingrese correo y contraseña", 400)

        if self._is_mock_user(email, password):
            return self._mock_login(email)

        user = self._local_login(email, password)
        if user:
            return user

        return self._java_login(email, password)

    def _get_credentials(self, data):
        return (data.get("email", "").lower().strip(), data.get("password"))

    def _is_mock_user(self, email, password):
        return email == "dev@kallpa.com" or (
            email == "admin@kallpa.com" and password == "123456"
        )

    def _local_login(self, email, password):
        user = User.query.filter_by(email=email, status="ACTIVO").first()

        if not user or not check_password_hash(user.password, password):
            return None

        self._sync_java_data_if_needed(user, email, password)

        token = generate_token(
            {
                "sub": user.external_id,
                "email": user.email,
                "role": user.role,
            }
        )

        return {
            "status": "ok",
            "msg": "Login exitoso",
            "token": token,
            "user": {
                "external_id": user.external_id,
                "email": user.email,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "role": user.role,
            },
            "code": 200,
        }

    def _sync_java_data_if_needed(self, user, email, password):
        if user.java_external:
            return

        try:
            response = requests.post(
                f"{Config.PERSON_API_URL}/login",
                json={"email": email, "password": password},
                timeout=3,
            )

            if response.status_code == 200:
                java_user = response.json().get("data", {})
                user.java_external = java_user.get("external")
                user.java_token = java_user.get("token")
                db.session.commit()

        except Exception as e:
            print(f"No se pudo sincronizar Java: {e}")

    def _java_login(self, email, password):
        try:
            response = requests.post(
                f"{Config.PERSON_API_URL}/login",
                json={"email": email, "password": password},
                timeout=3,
            )

            if response.status_code != 200:
                return error_response("Credenciales inválidas", 400)

            java_user = response.json().get("data", {})
            token = java_user.get("token", "").replace("Bearer ", "")

            return {
                "status": "ok",
                "msg": "Login Exitoso (Docker)",
                "token": token,
                "user": java_user,
                "code": 200,
            }

        except Exception:
            return error_response("No se pudo conectar al sistema externo", 500)

    def _mock_login(self, email):
        token = generate_token(
            {
                "sub": "usuario-mock-bypass",
                "email": email,
                "role": "ADMINISTRADOR",
            }
        )

        return {
            "status": "ok",
            "msg": "Login MOCK",
            "token": token,
            "user": {
                "external_id": "usuario-mock-bypass",
                "email": email,
                "role": "ADMINISTRADOR",
            },
            "code": 200,
        }

    def refresh_token(self, token: str):
        """Genera un nuevo token a partir del token actual (JWT Python)."""
        import jwt
        from flask import current_app

        if not token or not token.strip():
            return error_response("Token no proporcionado", 401)

        # Solo refrescamos tokens JWT Python (formato x.y.z)
        if token.count(".") != 2:
            return error_response("No se puede extender esta sesión", 400)

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return error_response("Token expirado. Inicia sesión nuevamente.", 401)
        except jwt.InvalidTokenError:
            return error_response("Token inválido", 401)

        user_data = payload.get("sub") or payload.get("external_id")
        if not user_data:
            return error_response("Token inválido", 401)

        new_token = generate_token(
            {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
        )

        return {
            "status": "ok",
            "msg": "Sesión extendida",
            "token": new_token,
            "code": 200,
        }
