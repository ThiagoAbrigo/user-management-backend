from app import db
import uuid


class Test(db.Model):
    __tablename__ = "test"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    frequency_months = db.Column(db.Integer, nullable=False)  # 3 o 6 meses
    status = db.Column(db.String(30), nullable=False, default="Activo")
    exercises = db.relationship("TestExercise", backref="test", lazy=True)