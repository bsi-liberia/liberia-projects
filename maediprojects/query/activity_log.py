import datetime
import json
from maediprojects.extensions import db
from maediprojects import models


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def activity_add_log(activity_id, user_id, mode=None, target=None, target_id=None, old_value=None, value=None):
    activity_log = models.ActivityLog()
    activity_log.activity_id = activity_id
    activity_log.user_id = user_id
    activity_log.mode = unicode(mode)
    activity_log.target = unicode(target)
    activity_log.target_id = target_id
    activity_log.old_value = json.dumps(old_value, cls=JSONEncoder) if old_value != None else None
    activity_log.value = json.dumps(value, cls=JSONEncoder) if value != None else None
    db.session.add(activity_log)
    db.session.commit()
    return activity_log


def activity_updated(activity_id, update_data=False):
    activity = models.Activity.query.filter_by(id=activity_id).first()
    if not activity:
        return False
    activity.updated_date = datetime.datetime.utcnow()
    db.session.add(activity)
    db.session.commit()
    if update_data:
        activity_add_log(activity_id, **update_data)
    return True
