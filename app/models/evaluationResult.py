from app import db
import uuid


class EvaluationResult(db.Model):
    __tablename__ = "evaluation_result"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    evaluation_id = db.Column(
        db.Integer, db.ForeignKey("evaluation.id"), nullable=False
    )
    test_exercise_id = db.Column(
        db.Integer, db.ForeignKey("test_exercise.id"), nullable=False
    )
    value = db.Column(db.Float, nullable=False)
    
    exercise = db.relationship("TestExercise")