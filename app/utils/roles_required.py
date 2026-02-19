from functools import wraps
from flask import jsonify, request
from app.utils.jwt_required import jwt_required

def roles_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required
        def wrapper(*args, **kwargs):
            user = getattr(request, "user", None)

            if not user:
                return jsonify({
                    "status": "error",
                    "msg": "No autenticado",
                    "code": 401
                }), 401

            user_role = user.get("role") or user.get("rol")

            if user_role not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "msg": "No autorizado",
                    "code": 403
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
