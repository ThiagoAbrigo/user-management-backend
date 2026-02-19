from app.models.activityLog import ActivityLog
from app import db

def log_activity(type, title, description):
    activity = ActivityLog(
        type=type,
        title=title,
        description=description,
    )
    db.session.add(activity)