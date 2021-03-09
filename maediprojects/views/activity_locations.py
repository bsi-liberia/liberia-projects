from maediprojects.views.api import jsonify
from maediprojects.query import user as quser
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation

from flask import Blueprint, request, abort
from flask_login import current_user

from flask_jwt_extended import (
    jwt_required, jwt_optional
)
from maediprojects.lib import util
from maediprojects import models


blueprint = Blueprint('activity_locations', __name__, url_prefix='/api/activity_locations')


@blueprint.route("/")
@jwt_optional
@quser.permissions_required("view")
def api_all_activity_locations():
    """GET returns a list of all locations."""
    query = models.ActivityLocation.query.join(
        models.Activity
    )
    query = qactivity.filter_activities_for_permissions(query)
    query = query.outerjoin(
                    models.ActivityFinances).filter(
        models.ActivityFinances.transaction_date >= '2019-01-01'
        )
    activitylocations = query.all()
    locations = list(map(lambda al: ({
        'locationID': al.id,
        'latitude': al.locations.latitude,
        'longitude': al.locations.longitude,
        'latlng': [ al.locations.latitude, al.locations.longitude ],
        'name': al.locations.name,
        "title": al.activity.title,
        "id": al.activity_id}),
        activitylocations))
    return jsonify(locations = locations)


@blueprint.route("/<activity_id>/", methods=["POST", "GET"])
@jwt_optional
def api_activity_locations(activity_id):
    """GET returns a list of all locations for a given activity_id.
    POST also accepts locations to be added or deleted."""
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    if request.method == "POST":
        if not quser.check_permissions("edit", None, activity_id): return abort(403)
        request_data = request.get_json()
        if request_data["action"] == "add":
            result = qlocation.add_location(activity_id, request_data["location_id"])
        elif request_data["action"] == "delete":
            result = qlocation.delete_location(activity_id, request_data["location_id"])
        return str(result)
    elif request.method == "GET":
        if not quser.check_permissions("view"): return abort(403)
        locations = list(map(lambda x: x.as_dict(),
                         qactivity.get_activity(activity_id).locations))
        return jsonify(locations = locations)
