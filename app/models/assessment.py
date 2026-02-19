import uuid
from app import db
from datetime import date

class Assessment(db.Model):
    __tablename__ = "assessment"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False, default=date.today)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    waistPerimeter = db.Column(db.Float, nullable=False)
    armPerimeter = db.Column(db.Float, nullable=True)
    legPerimeter = db.Column(db.Float, nullable=True)
    calfPerimeter = db.Column(db.Float, nullable=True) 
    status = db.Column(db.String(30), nullable=False)

    def saveResults(self):
        db.session.add(self)
        db.session.commit()
