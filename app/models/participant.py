from app import db
import uuid

class Participant(db.Model):
    __tablename__ = "participant"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    program = db.Column(db.String(50), nullable=True)  # "INICIACION" or "FUNCIONAL"
    java_external = db.Column(db.String(100), nullable=True)  # ID externo del microservicio Java
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Si también es User (docente/pasante)
    assessments = db.relationship("Assessment", backref="participant", lazy=True)


    def __repr__(self):
        return f"<Participant {self.firstName} {self.lastName}>"

    def authenticate(self, email, dni):
        return self.email == email and self.dni == dni