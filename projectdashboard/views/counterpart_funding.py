from flask import Blueprint, request, abort

from flask_jwt_extended import (
    jwt_required
)

from projectdashboard.views.api import jsonify
from projectdashboard.query import user as quser
from projectdashboard.query import activity as qactivity
from projectdashboard.query import counterpart_funding as qcounterpart_funding
from projectdashboard.lib import util


blueprint = Blueprint('counterpart_funding', __name__,
                      url_prefix='/api/counterpart_funding')


@blueprint.route("/<activity_id>/", methods=["POST", "GET"])
@jwt_required()
@quser.permissions_required("edit")
def api_activity_counterpart_funding(activity_id):
    activity = qactivity.get_activity(activity_id)
    if activity is None:
        return abort(404)
    """GET returns a list of all counterpart funding for a given activity_id.
    POST also accepts counterpart funding data to be added, deleted, updated."""
    if request.method == "POST":
        request_data = request.get_json()
        if request_data["action"] == "add":
            required_date = util.fq_fy_to_date(1,
                                               int(request_data["required_fy"])).date().isoformat()
            data = {
                "required_value": request_data["required_value"],
                "required_date": required_date,
                "budgeted": False,
                "allotted": False,
                "disbursed": False,
            }
            result = qcounterpart_funding.add_entry(activity_id, data)
            cf = result.as_dict()
            cf["required_fy"], fq = util.date_to_fy_fq(cf["required_date"])
            return jsonify(counterpart_funding=cf)
        elif request_data["action"] == "delete":
            result = qcounterpart_funding.delete_entry(
                activity_id, request_data["id"])
            if result:
                return jsonify(result=True)
            return abort(500)
        elif request_data["action"] == "update":
            attr = request_data['attr']
            value = request_data['value']
            if value == "true":
                value = True
            elif value == "false":
                value = False
            if attr == "required_fy":
                attr = "required_date"
                value = util.fq_fy_to_date(1,
                                           int(value)).date().isoformat()
            data = {
                'activity_id': activity_id,
                'attr': attr,
                'value': value,
                'id': request_data['id'],
            }
            update_status = qcounterpart_funding.update_entry(data)
            if update_status:
                return jsonify(result=True)
            return abort(500)
        return str(result)
    elif request.method == "GET":
        def to_fy(counterpart_funding):
            cf = counterpart_funding.as_dict()
            cf["required_fy"], fq = util.date_to_fy_fq(
                counterpart_funding.required_date)
            return cf
        counterpart_funding = sorted(
            list(map(lambda cf: to_fy(cf),
                     qactivity.get_activity(activity_id).counterpart_funding)),
            key=lambda x: x["required_date"])
        return jsonify(counterpart_funding=counterpart_funding,
                       fiscal_years=range(2013, 2025))
