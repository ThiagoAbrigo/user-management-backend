from app import db
import uuid

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)

    participant = db.relationship("Participant", backref=db.backref("attendances", lazy=True))
    schedule = db.relationship("Schedule", backref=db.backref("attendances", lazy=True))

    class Status:
        PRESENT = "present"
        ABSENT = "absent"
