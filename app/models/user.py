from app import db
import uuid

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )

    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)  # Dirección del usuario

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)  # docente | pasante
    status = db.Column(db.String(20), nullable=False)  # activo | inactivo
    java_external = db.Column(db.String(100), nullable=True)  # ID externo del microservicio Java
    java_token = db.Column(db.String(500), nullable=True)  # Token Bearer de Java para sincronización

    # Si este usuario (docente/pasante) también es participante del club
    participant = db.relationship(
        "Participant", backref="user", uselist=False, foreign_keys="Participant.user_id"
    )
