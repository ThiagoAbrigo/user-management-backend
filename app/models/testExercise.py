from app import db
import uuid

class TestExercise(db.Model):
    __tablename__ = "test_exercise"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  
    # Ej: repeticiones, segundos, metros