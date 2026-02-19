from flask import request
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self):
        self.service = AuthService()

    def login(self, data):
        return self.service.login(data)

    def refresh(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"status": "error", "msg": "Token no proporcionado", "code": 401}
        token = auth_header.split(" ", 1)[1]
        return self.service.refresh_token(token)
