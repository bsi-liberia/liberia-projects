import datetime

from sqlalchemy import *

from projectdashboard import models
from projectdashboard.extensions import db


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")

def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")

def add_or_update_activity_milestone(data):
    checkM = models.ActivityMilestone.query.filter_by(
        activity_id=data["activity_id"],
        milestone_id=data["milestone_id"]
        ).first()
    if not checkM:
        checkM = models.ActivityMilestone()
        checkM.activity_id = data["activity_id"]
        checkM.milestone_id = data["milestone_id"]
    setattr(checkM, data["attribute"], data["value"])
    db.session.add(checkM)
    db.session.commit()
    return True
