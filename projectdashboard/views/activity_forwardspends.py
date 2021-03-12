from projectdashboard.views.api import jsonify
from projectdashboard.query import user as quser
from projectdashboard.query import activity as qactivity
from projectdashboard.query import finances as qfinances

from flask import Blueprint, request, abort
from flask_login import current_user

from flask_jwt_extended import (
    jwt_required
)
from projectdashboard.lib import util
from projectdashboard import models

from collections import OrderedDict

blueprint = Blueprint('activity_forwardspends', __name__, url_prefix='/api/activity_forwardspends')


@blueprint.route("/<activity_id>/<fiscal_year>/", methods=["GET", "POST"])
@blueprint.route("/<activity_id>/", methods=["GET", "POST"])
@jwt_required()
@quser.permissions_required("edit")
def api_activity_forwardspends(activity_id, fiscal_year=True):
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    """GET returns a list of all forward spend data for a given activity_id.
    POST updates value for a given forwardspend_id."""
    if request.method == "GET":
        if not fiscal_year==False:
            data = qactivity.get_activity(activity_id).forwardspends
            forwardspends = list(map(lambda fs_db: fs_db.as_dict(),
                             qactivity.get_activity(activity_id).forwardspends))
            # Return fiscal years here
            years = sorted(set(map(lambda fs: util.date_to_fy_fq(fs["value_date"])[0],
                             forwardspends)))
            out = OrderedDict()
            for year in years:
                out[year] = OrderedDict({"year": "FY{}".format(util.fy_to_fyfy(str(year))), "total_value": 0.00})
                for forwardspend in sorted(forwardspends, key=lambda k: k["value_date"]):
                    if util.date_to_fy_fq(forwardspend["period_start_date"])[0] == year:
                        fq = util.date_to_fy_fq(forwardspend["period_start_date"])[1]
                        out[year]["Q{}".format(fq)] = forwardspend
                        out[year]["total_value"] += float(forwardspend["value"])
            out = list(out.values())
            quarters = util.make_quarters_text(util.LR_QUARTERS_MONTH_DAY)
            return jsonify(forwardspends=out, quarters=quarters)
        else:
            data = qactivity.get_activity(activity_id).forwardspends
            forwardspends = list(map(lambda fs_db: fs_db.as_dict(),
                             qactivity.get_activity(activity_id).forwardspends))
            years = sorted(set(map(lambda fs: fs["value_date"].year,
                             forwardspends)))
            out = OrderedDict()
            for year in years:
                out[year] = {"year": year, "total_value": 0.00}
                for forwardspend in forwardspends:
                    if forwardspend["period_start_date"].year == year:
                        fq = MONTHS_QUARTERS[forwardspend["period_start_date"].month]
                        out[year]["Q{}".format(fq)] = forwardspend
                        out[year]["total_value"] += float(forwardspend["value"])
            out = list(out.values())
            quarters = util.make_quarters_text(util.QUARTERS_MONTH_DAY)
            return jsonify(forwardspends=out, quarters=quarters)

    elif request.method == "POST":
        request_data = request.get_json()
        if request_data["value"] in (None, " ", ""):
            value = 0
        else:
            value = request_data["value"]
        data = {
            "id": request_data["id"],
            "value": value
        }
        update_status = qfinances.update_fs_attr(data)
        if update_status == True:
            return "success"
        return "error"

@blueprint.route("/<activity_id>/update_forwardspends/", methods=['POST'])
@jwt_required()
@quser.permissions_required("edit")
def forwardspends_edit_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'finances_id': request.form['finances_id'],
    }
    update_status = qfinances.update_attr(data)
    if update_status == True:
        return "success"
    return "error"
