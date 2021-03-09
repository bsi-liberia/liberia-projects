from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from maediprojects.views.api import jsonify
from maediprojects.query import user as quser
from maediprojects import models


blueprint = Blueprint('activity_log', __name__, url_prefix='/api/activity-log')

@blueprint.route("/")
@jwt_required
@quser.permissions_required("edit")
def activity_log():
    offset = (int(request.args.get("page", 1))-1)*10
    count = models.ActivityLog.query.count()
    user_id = request.args.get("user_id", None)
    activitylogs = quser.activitylog(offset=offset,
        user_id=user_id)
    def simple_log(al):
        return {
            "id": al.id,
            "user": {
                "id": al.user_id,
                "username": al.user.username
            },
            "activity": {
                "id": al.activity_id,
                "title": al.activity.title
            },
            "mode": {
                "id": al.mode,
                "text": al.mode_text
            },
            "date": al.log_date.replace(microsecond=0).isoformat(),
            "target": {
                "id": al.target_id,
                "text": al.target_text
            }
        }
    return jsonify(
        count = count,
        items = list(map(lambda al: simple_log(al), activitylogs)))


@blueprint.route("/<int:activitylog_id>.json")
@jwt_required
@quser.permissions_required("edit")
def activity_log_detail(activitylog_id):
    al = quser.activitylog_detail(activitylog_id)
    def get_object(target, target_text, id):
        if not getattr(models, target).query.get(id):
            return None, None
        if target == "ActivityLocation":
            return "Location", getattr(models, target).query.get(id).locations.as_dict()
        elif target == "ActivityFinances":
            return "Financial data", getattr(models, target).query.get(id).as_simple_dict()
        elif target == "ActivityFinancesCodelistCode":
            return "Financial data", getattr(models, target).query.get(id).activityfinances.as_simple_dict()
        else:
            return target_text.title(), getattr(models, target).query.get(id).as_dict()
        return None, None

    _obj_title, _obj = get_object(al.target, al.target_text, al.target_id)

    return jsonify(data={
        "id": al.id,
        "user": {
            "id": al.user_id,
            "username": al.user.username
        },
        "activity": {
            "id": al.activity_id,
            "title": al.activity.title
        },
        "mode": {
            "id": al.mode,
            "text": al.mode_text
        },
        "date": al.log_date.replace(microsecond=0).isoformat(),
        "target": {
            "id": al.target_id,
            "text": al.target_text,
            "obj_title": _obj_title,
            "obj": _obj
        },
        "value": json.loads(al.value) if al.value else None,
        "old_value": json.loads(al.old_value) if al.old_value else None
    })
