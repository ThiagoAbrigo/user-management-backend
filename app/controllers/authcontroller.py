from werkzeug.security import check_password_hash
from app.utils.responses import success_response, error_response
from app.models import Participant


class AuthController:

    def login(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return error_response("Email y contraseña son obligatorios"), 400

        participant = Participant.query.filter_by(email=email).first()

        if not participant:
            return error_response("Usuario no encontrado"), 404

        if not check_password_hash(participant.password, password):
            return error_response("Contraseña incorrecta"), 401

        responsible = participant.responsibles[0] if participant.responsibles else None
        return (
            success_response(
                "Login exitoso",
                {
                    "id": participant.id,
                    "external_id": participant.external_id,
                    "name": participant.name,
                    "email": participant.email,
                    "role": participant.role,
                    "status": participant.status,
                    "age": participant.age,
                    "dni": participant.dni,
                    "estate": participant.estate,
                    "address": participant.address,
                    "nombreResponsable": responsible.name if responsible else None,
                    "dniResponsable": responsible.dni if responsible else None,
                    "telefonoResponsable": responsible.phone if responsible else None,
                },
            ),
            200,
        )
