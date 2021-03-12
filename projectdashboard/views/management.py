from projectdashboard.views.api import jsonify
from projectdashboard.query import user as quser
from projectdashboard.query import monitoring as qmonitoring
from projectdashboard.query import organisations as qorganisations

from flask import Blueprint, request
from flask_login import current_user

from flask_jwt_extended import (
    jwt_required
)
from projectdashboard.lib import util
from projectdashboard import models


blueprint = Blueprint('management', __name__, url_prefix='/api/management')


def generate_reporting_organisation_checklist(reporting_orgs, _response_statuses):
    response_statuses = dict(map(lambda r: (r["id"], r), _response_statuses))
    response_statuses[0] = {
        'name': 'Donor did not respond',
        'icon_class': 'far',
        'icon': 'times-circle',
        'colour': 'text-secondary'}
    ros_fiscal_years = qmonitoring.forwardspends_ros("current")
    ros_fiscal_years_previous = qmonitoring.forwardspends_ros("previous")
    ros_fiscal_years_next = qmonitoring.forwardspends_ros("next")
    ros_disbursements = qmonitoring.fydata_ros("todate")
    def make_status(ro, qtr, disb_value):
        if disb_value:
            return response_statuses.get(3) #FIXME this is the database ID for donor responded with data
        quarters = util.Last4Quarters().list_of_quarters()
        if ro.responses_fys.get(quarters.get(qtr)):
            return response_statuses.get(ro.responses_fys.get(quarters.get(qtr)))
        return response_statuses.get(0)

    def annotate_ro(ro):
        _ro = ro.as_dict()
        _ro["responses_fys"] = ro.responses_fys
        _ro["activities_count"] = ro.activities_count
        _ro["forwardspends"] = {
            "current": {
                'value': ros_fiscal_years.get(ro.id, 0.00),
                'status': make_status(ro, None, ros_fiscal_years.get(ro.id)),
            },
            "previous": {
                'value': ros_fiscal_years_previous.get(ro.id, 0.00),
                'status': make_status(ro, None, ros_fiscal_years_previous.get(ro.id)),
            },
            "next": {
                'value': ros_fiscal_years_next.get(ro.id, 0.00),
                'status': make_status(ro, None, ros_fiscal_years_next.get(ro.id)),
            }
        }
        _ro["disbursements"] = dict([
            (qtr, {
                'value': ros_disbursements.get((ro.id, qtr), 0.00),
                'status': make_status(ro, qtr, ros_disbursements.get((ro.id, qtr)))
            }) for qtr in [u"Q1", u"Q2", u"Q3", u"Q4"]])
        return _ro
    return list(map(lambda ro: annotate_ro(ro), reporting_orgs))


@blueprint.route("/reporting_orgs_user.json", methods=["GET", "POST"])
@jwt_required()
def reporting_orgs_user():
    if request.method == "POST":
        if ("organisation_id" in request.json) and ("response_id" in request.json):
            qmonitoring.update_organisation_response(
                request.json)
        return jsonify(result=True)
    if ("user_id" in request.args) or ("admin" not in current_user.roles_list): # FIXME Change to Roles
        reporting_orgs = qorganisations.get_reporting_orgs(user_id=request.args.get('user_id', current_user.id))
        user = models.User.query.get(request.args.get('user_id', current_user.id))
        user_name = user.name
        user_id = user.id
    else:
        reporting_orgs = qorganisations.get_reporting_orgs()
        user_name = None
        user_id = None
    if "admin" in current_user.roles_list:
        users = list(map(lambda u: {'value': u.id, 'text': u.name},
            quser.users_with_role('desk-officer')))
    else:
        users = []
    response_statuses = list(map(lambda r: r.as_dict(), qmonitoring.response_statuses()))
    orgs = generate_reporting_organisation_checklist(reporting_orgs, response_statuses)

    data_collection_calendar = qmonitoring.generate_data_collection_calendar()

    return jsonify(
        orgs=orgs,
        previous_year = util.FY("previous").fy_fy(),
        current_year = util.FY("current").fy_fy(),
        next_year = util.FY("next").fy_fy(),
        list_of_quarters = util.Last4Quarters().list_of_quarters(),
        users=users,
        user_name=user_name,
        user_id=user_id,
        statuses=response_statuses,
        data_collection_calendar=data_collection_calendar
        )


@blueprint.route("/reporting_orgs.json")
@jwt_required()
def reporting_orgs():
    reporting_orgs = qorganisations.get_reporting_orgs()
    response_statuses = list(map(lambda r: r.as_dict(), qmonitoring.response_statuses()))
    orgs = generate_reporting_organisation_checklist(reporting_orgs, response_statuses)
    return jsonify(
        orgs=orgs,
        previous_year = util.FY("previous").fy_fy(),
        current_year = util.FY("current").fy_fy(),
        next_year = util.FY("next").fy_fy(),
        list_of_quarters = util.Last4Quarters().list_of_quarters()
        )


@blueprint.route("/reporting_orgs/summary.json")
@jwt_required()
def reporting_orgs_summary():
    reporting_orgs = qorganisations.get_reporting_orgs()
    response_statuses = list(map(lambda r: r.as_dict(), qmonitoring.response_statuses()))
    orgs = generate_reporting_organisation_checklist(reporting_orgs, response_statuses)

    def generate_summary(list_of_quarters, orgs):
        out = dict(map(lambda q: (q, { 'True': 0, 'False': 0, "Total": 0 }), list_of_quarters.keys()))
        for ro in orgs:
            for disb_q, disb_v in ro["disbursements"].items():
                if disb_v["status"]["name"]=="Donor responded with data":
                    out[disb_q]['True'] += 1
                else:
                    out[disb_q]['False'] += 1
                out[disb_q]["Total"] += 1
        return out

    list_of_quarters = util.Last4Quarters().list_of_quarters()
    summary = generate_summary(list_of_quarters, orgs)

    return jsonify(
        summary=summary,
        current_year = util.FY("current").fy_fy(),
        previous_year = util.FY("previous").fy_fy(),
        list_of_quarters = list_of_quarters
        )