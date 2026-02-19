from app import db
import uuid
from datetime import date

class Evaluation(db.Model):
    __tablename__ = "evaluation"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    general_observations = db.Column(db.String(255))

    results = db.relationship("EvaluationResult", backref="evaluation", lazy=True)
    test = db.relationship("Test")