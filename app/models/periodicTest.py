from app.models.assessment import Assessment
from app import db
import uuid


class PeriodicTest(Assessment):
    __tablename__ = "periodic_test"

    id = db.Column(db.Integer, db.ForeignKey("assessment.id"), primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    burpees = db.Column(db.Integer, nullable=False)
    squats = db.Column(db.Integer, nullable=False)
    verticalJump = db.Column(db.Integer, nullable=False)
    plank = db.Column(db.Integer, nullable=False)
    pullUps = db.Column(db.Integer, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "periodic_test",
    }
