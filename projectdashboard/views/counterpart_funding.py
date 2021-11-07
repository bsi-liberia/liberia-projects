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
    # GET returns a list of all counterpart funding for a given activity_id.
    # POST also accepts counterpart funding data to be added, deleted, updated.
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
            counterpart_fund = result.as_dict()
            counterpart_fund["required_fy"], _ = util.date_to_fy_fq(
                counterpart_fund["required_date"])
            return jsonify(counterpart_funding=counterpart_fund)
        elif request_data["action"] == "delete":
            if 'year' in request_data:
                result = qcounterpart_funding.delete_year(
                    activity_id, request_data["year"])
            elif 'type' in request_data:
                result = qcounterpart_funding.delete_type(
                    activity_id, request_data["type"])
            if result:
                return jsonify(result=True)
            return abort(500)
        elif request_data["action"] == "update":
            year = request_data['year']
            value = request_data['value']
            data = {
                'activity_id': activity_id,
                'year': year,
                'value': value,
                'type': request_data['type'],
            }
            update_status = qcounterpart_funding.update_entry(data)
            if update_status:
                return jsonify(result=True)
            return abort(500)
        return str(result)
    elif request.method == "GET":
        def to_fy(counterpart_funding):
            counterpart_fund = counterpart_funding.as_dict()
            if counterpart_funding.required_date == None:
                counterpart_fund["year"] = 'total'
            else:
                counterpart_fund["year"] = counterpart_funding.fiscal_period.fiscal_year.name
            if counterpart_funding.required_funding_type == None:
                counterpart_fund["type"] = 'total'
            else:
                counterpart_fund["type"] = counterpart_funding.required_funding_type
            return counterpart_fund
        counterpart_funding = [to_fy(counterpart_fund) for counterpart_fund in
            qactivity.get_activity(activity_id).counterpart_funding]
        fys = [str(fy) for fy in util.available_fys(10)]
        return jsonify(counterpart_funding=counterpart_funding,
                       fiscal_years=fys)
