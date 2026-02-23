from app import db
import uuid

class Participant(db.Model):
    __tablename__ = "participant"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    estate = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # Si también es User (docente/pasante)
