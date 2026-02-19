from app import db
import uuid


class Schedule(db.Model):
    __tablename__ = "schedule"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    dayOfWeek = db.Column(db.String(20), nullable=True)
    startTime = db.Column(db.String(10), nullable=False)
    endTime = db.Column(db.String(10), nullable=False)
    maxSlots = db.Column(db.Integer, nullable=False, default=30)
    program = db.Column(db.String(100), nullable=False)
    
    startDate = db.Column(db.String(10), nullable=True)
    endDate = db.Column(db.String(10), nullable=True)
    specificDate = db.Column(db.String(10), nullable=True)
    isRecurring = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default="active")

    def __repr__(self):
        return f"<Schedule {self.name}>"
