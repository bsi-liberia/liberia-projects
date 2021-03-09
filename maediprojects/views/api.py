import datetime
import json
import re
from collections import OrderedDict

from flask import Blueprint, request, \
    url_for, Response, current_app, abort
from flask_login import current_user
import sqlalchemy as sa
from sqlalchemy.sql import func
import requests
from flask_jwt_extended import (
    jwt_required, jwt_optional
)

from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import finances as qfinances
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.query import organisations as qorganisations
from maediprojects.query import milestones as qmilestone
from maediprojects.query import generate_csv as qgenerate_csv
from maediprojects.query import user as quser
from maediprojects.lib import util, spreadsheet_headers
from maediprojects.lib.codelists import get_codelists_lookups, get_codelists
from maediprojects.lib.util import MONTHS_QUARTERS
from maediprojects import models
from maediprojects.extensions import db


blueprint = Blueprint('api', __name__, url_prefix='/', static_folder='../static')


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date)):
            return obj.isoformat()
        elif (type(obj) is {}.values().__class__) or (type(obj) is {}.keys().__class__):
            return list(obj)
        elif (type(obj) is range):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs), cls=JSONEncoder),
        mimetype='application/json')


@blueprint.route("/api/")
def api():
    return jsonify(
        activities = url_for('activities.api_activities_country', _external=True),
        data = {
            "iati": url_for("iati.api_list_iati_files", _external=True),
            "csv": url_for("exports.activities_csv", _external=True)
        }
    )



@blueprint.route("/api/spreadsheet_headers.json")
def spreadsheet_field_names():
    headers = spreadsheet_headers.headers
    selected_mtef_headers = qgenerate_csv.mtef_fys()
    mtef_headers = qgenerate_csv.mtef_fys(start=2013, end=2025)
    selected_disb_headers = [util.previous_fy_fq()]
    disb_headers = qgenerate_csv.disb_fy_fqs()
    selected_counterpart_headers = qgenerate_csv.counterpart_fys()
    counterpart_headers = qgenerate_csv.counterpart_fys(start=2013, end=2025)
    return jsonify(headers=headers,
        mtef_headers=mtef_headers,
        disbursement_headers=disb_headers,
        counterpart_funding_headers=counterpart_headers,
        selected={
            "disbursements": spreadsheet_headers.headers_disb_template_1 + selected_disb_headers + spreadsheet_headers.headers_disb_template_2,
            "mtef": spreadsheet_headers.headers_mtef_template_1 + selected_counterpart_headers + selected_mtef_headers + spreadsheet_headers.headers_mtef_template_2
        })


@blueprint.route("/api/filters/currency.json")
def filters_currency():
    def annotate(currency):
        _currency = currency.as_dict()
        _currency["display_name"] = "{} - {}".format(currency.code, currency.name)
        return _currency
    return jsonify(currencies=list(map(lambda c: annotate(c), qexchangerates.get_currencies())))


@blueprint.route("/api/filters/available_fys.json")
def available_fys():
    fy, _ = util.FY("previous").numeric()
    return jsonify(fys=util.available_fys_as_dict(),
        current_fy=fy)


@blueprint.route("/api/filters/available_fys_fqs.json")
def available_fys_fqs():
    def mtef_or_disbursements():
        """Set reporting functionality to highlight MTEF or disbursement
        data import by default, depending on where we are in the year"""
        budget_preparation_month = 2
        if datetime.datetime.utcnow().date().month == budget_preparation_month:
            return "mtef"
        else:
            return "disbursements"
    return jsonify(
        fys=util.available_fys(),
        fys_fqs=util.available_fy_fqs_as_dict(),
        current_fy=util.FY("current").fy_fy(),
        previous_fy_fq=util.previous_fy_fq(),
        mtef_or_disbursements=mtef_or_disbursements())


@blueprint.route("/api/filters/reporting_organisation.json")
def filters_reporting_organisation():
    return jsonify(reporting_organisations=list(map(lambda ro: ro.as_dict(), qorganisations.get_reporting_orgs())))


@blueprint.route("/api/user-results/")
@jwt_required
@quser.permissions_required("view")
def api_activities_user_results():
    activities = qactivity.list_activities_by_filters({'result_indicator_periods': True}, "results-data-entry")
    return jsonify(
            activities=[{
                "id": activity.id,
                "title": activity.title,
                "funding_org": ", ".join(list(map(lambda o: o.name, activity.funding_organisations))),
                "results_average": activity.results_average,
                "permissions": {
                    "data_entry": ("results-data-entry" in current_user.roles_list) or ("results-data-design" in current_user.roles_list) or ("admin" in current_user.roles_list),
                    "data_design": ("results-data-design" in current_user.roles_list) or ("admin" in current_user.roles_list)
                }
                } for activity in activities]
        )


@blueprint.route("/api/api_activity_milestones/<activity_id>/", methods=["GET", "POST"])
@jwt_optional
@quser.permissions_required("view")
def api_activity_milestones(activity_id):
    if request.method == "POST":
        request_data = request.get_json()
        milestone_id = request_data["milestone_id"]
        attribute = request_data["attr"]
        value = request_data["value"]
        update_status = qmilestone.add_or_update_activity_milestone({
                    "activity_id": activity_id,
                    "milestone_id": milestone_id,
                    "attribute": attribute,
                    "value": value})
        if update_status == True:
            return "success"
        return "error"
    else:
        activity = qactivity.get_activity(activity_id)
        if activity == None: return abort(404)
        return jsonify(milestones=activity.milestones_data)


@blueprint.route("/api/codelists.json", methods=["GET", "POST"])
@jwt_required
@quser.permissions_required("view")
def api_codelists():
    if (request.method == "GET"):
        return jsonify(
                codelists = get_codelists(),
                organisations = list(map(lambda o: o.as_dict(), qorganisations.get_organisations())))
    elif (request.method == "POST"):
        method = request.json["method"]
        codelist = request.json["codelist"]
        if ((method == "add") and (codelist == "fund-source")):
            new_fund_source = qfinances.add_fund_source(request.json)
            return jsonify(id = new_fund_source.id)
        return abort(500)


@blueprint.route("/api/activity_locations/")
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

@blueprint.route("/api/activity_locations/<activity_id>/", methods=["POST", "GET"])
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

@blueprint.route("/api/locations/<country_code>/")
def api_locations(country_code):
    """Returns locations and tries to sort them. Note that there may be cases where
    this will break as the geonames data does not always contain
    good information about the hierarchical relationships between locations."""
    locations = list(map(lambda x: x.as_dict(),
                     qlocation.get_locations_country(country_code)))
    for i, location in enumerate(locations):
        if location["feature_code"] == "ADM2":
            locations[i]["name"] = " - %s" % location["name"]
    return jsonify(locations = locations)


@blueprint.route("/api/sectors.json")
def api_sectors():
    sector_totals = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("total_disbursement"),
        models.CodelistCode.code,
        models.CodelistCode.name,
        func.strftime('%Y', func.date(models.ActivityFinances.transaction_date, 'start of month', '-6 month')).label("fiscal_year")
    ).join(
        models.Activity,
        models.ActivityFinancesCodelistCode,
        models.CodelistCode
    ).filter(
        models.ActivityFinances.transaction_type == u"D",
        models.ActivityFinancesCodelistCode.codelist_id == u"mtef-sector"
    ).group_by(
        models.CodelistCode.name,
        models.CodelistCode.code,
        "fiscal_year"
    ).all()
    return jsonify(sectors = list(map(lambda s: {
        "name": s.name,
        "value": round(s.total_disbursement, 2),
        "code": s.code,
        "fy": s.fiscal_year
    }, sector_totals)))


@blueprint.route("/api/sectors_C_D.json")
def api_sectors_C_D():
    query = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("total_value"),
        models.ActivityFinances.transaction_type,
        models.CodelistCode.code,
        models.CodelistCode.name,
        models.Activity.domestic_external,
        func.strftime('%Y', func.date(models.ActivityFinances.transaction_date, 'start of month', '-6 month')).label("fiscal_year")
    ).join(
        models.Activity,
        models.ActivityFinancesCodelistCode,
        models.CodelistCode
    ).filter(
        models.CodelistCode.codelist_code == u"mtef-sector",
        models.CodelistCode.name != u"",
        models.Activity.domestic_external == 'external'
    ).group_by(
        models.CodelistCode.name,
        models.CodelistCode.code,
        models.ActivityFinances.transaction_type,
        models.Activity.domestic_external,
        "fiscal_year"
    )
    query = qactivity.filter_activities_for_permissions(query)
    sector_totals = query.all()

    fy_query = db.session.query(
        func.sum(models.ActivityForwardSpend.value).label("total_value"),
        sa.sql.expression.literal("FS").label("transaction_type"),
        models.CodelistCode.code,
        models.CodelistCode.name,
        models.Activity.domestic_external,
        func.strftime('%Y', func.date(models.ActivityForwardSpend.period_start_date, 'start of month', '-6 month')).label("fiscal_year")
    ).join(
        models.Activity,
        models.ActivityCodelistCode,
        models.CodelistCode
    ).filter(
        models.CodelistCode.codelist_code == u"mtef-sector",
        models.CodelistCode.name != u"",
        models.Activity.domestic_external == 'external'
    ).group_by(
        models.CodelistCode.name,
        models.CodelistCode.code,
        "transaction_type",
        models.Activity.domestic_external,
        "fiscal_year"
    )
    fy_query = qactivity.filter_activities_for_permissions(fy_query)
    fy_sector_totals = fy_query.all()


    def append_path(root, paths):
        if paths:
            sector = root.setdefault("{}_{}_{}".format(paths.domestic_external, paths.fiscal_year, paths.name), {'Commitments': 0.0, 'Disbursements': 0.0, 'Allotments': 0.0, 'Disbursement Projection': 0.0})
            sector[{"C": "Commitments", "D": "Disbursements", "99-A": "Allotments", "FS": "Disbursement Projection"}[paths.transaction_type]] = paths.total_value
            sector["name"] = paths.name
            sector["code"] = paths.code
            sector["domestic_external"] = paths.domestic_external
            sector["fy"] = paths.fiscal_year
    root = {}
    for s in sector_totals: append_path(root, s)
    for s in fy_sector_totals: append_path(root, s)
    return jsonify(sectors = list(root.values()))


@blueprint.route("/api/activitylog.json")
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


@blueprint.route("/api/activitylog/<int:activitylog_id>.json")
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

