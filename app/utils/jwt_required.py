# app/utils/jwt_required.py
import jwt
from functools import wraps
from flask import request, jsonify, current_app

SESSION_ERROR_MSG = "Tu sesión ha terminado por seguridad. Por favor, vuelve a iniciar sesión para continuar con tus actividades."


def get_jwt_identity():
    """Obtiene el external_id del usuario del token JWT decodificado."""
    user_data = getattr(request, "user", None)
    if user_data:
        return (
            user_data.get("sub")
            or user_data.get("external_id")
            or user_data.get("external")
            or user_data.get("id")
        )
    return None


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return _unauthorized("No hay sesión activa. Por favor inicia sesión.")

        try:
            token = _extract_bearer_token(auth_header)
            request.user = _resolve_user_from_token(token)
        except Exception:
            return _unauthorized(SESSION_ERROR_MSG)

        return f(*args, **kwargs)

    return decorated


def _extract_bearer_token(auth_header):
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header")
    return parts[1]


def _resolve_user_from_token(token):
    if _is_python_jwt(token):
        return _decode_python_jwt(token)
    return _resolve_java_token(token)


def _is_python_jwt(token):
    return token.count(".") == 2


def _decode_python_jwt(token):
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def _resolve_java_token(token):
    from app.models.user import User

    user = (
        User.query.filter_by(java_token=f"Bearer {token}").first()
        or User.query.filter_by(java_token=token).first()
    )

    if not user:
        raise ValueError("Invalid Java token")

    return {
        "sub": user.external_id,
        "email": user.email,
        "role": user.role,
        "external_id": user.external_id,
    }


def _unauthorized(message):
    return jsonify({"msg": message, "code": 401}), 401
