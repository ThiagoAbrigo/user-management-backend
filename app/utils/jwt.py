import jwt
from datetime import datetime, timedelta
from flask import current_app


def generate_token(payload, expires_minutes=60):
    payload = payload.copy()
    payload["iat"] = datetime.utcnow()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)

    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
