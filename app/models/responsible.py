from app import db
import uuid


class Responsible(db.Model):
    __tablename__ = "responsible"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    participant = db.relationship(
        "Participant", backref=db.backref("responsibles", lazy=True)
    )

    def __repr__(self):
        return f"<Responsible {self.name}>"

    def authenticate(self, dni):
        return self.dni == dni
