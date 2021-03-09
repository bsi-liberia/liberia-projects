import datetime
import json
import re
from collections import OrderedDict

from flask import Blueprint, request, \
    url_for, Response, current_app, abort
from flask_login import login_required, current_user
import sqlalchemy as sa
from sqlalchemy.sql import func
import requests
from flask_jwt_extended import (
    jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, get_raw_jwt, jwt_optional
)

from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import finances as qfinances
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.query import codelists as qcodelists
from maediprojects.query import organisations as qorganisations
from maediprojects.query import generate as qgenerate
from maediprojects.query import milestones as qmilestone
from maediprojects.query import generate_csv as qgenerate_csv
from maediprojects.query import user as quser
from maediprojects.query import monitoring as qmonitoring
from maediprojects.query import reports as qreports
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
        activities = url_for('activities.api_activities_country', _external=True)
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


@blueprint.route("/api/reporting_orgs_user.json", methods=["GET", "POST"])
@jwt_required
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


@blueprint.route("/api/reporting_orgs.json")
@jwt_required
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


@blueprint.route("/api/reporting_orgs/summary.json")
@jwt_required
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


@blueprint.route("/api/activity_finances/<activity_id>/", methods=["POST", "GET"])
@jwt_required
@quser.permissions_required("edit")
def api_activity_finances(activity_id):
    """GET returns a list of all financial data for a given activity_id.
    POST also accepts financial data to be added or deleted."""
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    if request.method == "POST":
        request_data = request.get_json()
        if request_data["action"] == "add":
            # Fallbak to activity data
            print('classification_data', activity.classification_data)
            data = {
                "transaction_type": request_data["transaction_type"],
                "transaction_date": request_data["transaction_date"],
                "transaction_value": request_data["transaction_value"],
                "aid_type": request_data.get("aid_type", activity.aid_type),
                "finance_type": request_data.get("finance_type", activity.finance_type),
                "provider_org_id": request_data.get("provider_org_id", activity.funding_organisations[0].id),
                "receiver_org_id": request_data.get("receiver_org_id", activity.implementing_organisations[0].id),
                "fund_source_id": request_data.get("fund_source_id", None),
                "currency": request_data.get("currency", u"USD"),
                "classifications": {
                    "mtef-sector": request_data.get("mtef_sector",
                        activity.classification_data['mtef-sector']['entries'][0].codelist_code_id)
                }
            }
            result = qfinances.add_finances(activity_id, data).as_simple_dict()
        elif request_data["action"] == "delete":
            result = qfinances.delete_finances(activity_id, request.get_json()["transaction_id"])
        if result:
            return jsonify(result)
        else: return abort(500)
    elif request.method == "GET":
        finances = {
            'commitments': list(map(lambda t: t.as_dict(), activity.commitments)),
            'allotments': list(map(lambda t: t.as_dict(), activity.allotments)),
            'disbursements': list(map(lambda t: t.as_dict(), activity.disbursements))
        }
        fund_sources = list(map(lambda fs: {
            "id": fs.id, "name": fs.name
            }, models.FundSource.query.all()))
        return jsonify(
            finances = finances,
            fund_sources = fund_sources
        )

@blueprint.route("/api/activity_finances/<activity_id>/update_finances/", methods=['POST'])
@jwt_required
@quser.permissions_required("edit")
def finances_edit_attr(activity_id):
    request_data = request.get_json()
    data = {
        'activity_id': activity_id,
        'attr': request_data['attr'],
        'value': request_data['value'],
        'finances_id': request_data['finances_id'],
    }

    #Run currency conversion if:
    # we now set to automatic
    # we change the currency and have set to automatic
    if (data.get("attr") == "transaction_date") and (data.get("value") == ""):
        return abort(500)
    if (data.get("attr") == "currency_automatic") and (data.get("value") == True):
        # Handle update, and then return required data
        update_status = qexchangerates.automatic_currency_conversion(
            finances_id = data["finances_id"],
            force_update = True)
        return jsonify(update_status.as_dict())
    elif (data.get("attr") in ("currency", "transaction_date")):
        update_curency = qfinances.update_attr(data)
        update_status = qexchangerates.automatic_currency_conversion(
            finances_id = data["finances_id"],
            force_update = False)
        return jsonify(update_status.as_simple_dict())
    elif data["attr"] == "mtef_sector":
        data["attr"] = 'mtef-sector' #FIXME make consistent
        update_status = qfinances.update_finances_classification(data)
    else:
        update_status = qfinances.update_attr(data)
    if update_status:
        return jsonify(update_status.as_simple_dict())
    return abort(500)

@blueprint.route("/api/activity_counterpart_funding/<activity_id>/", methods=["POST", "GET"])
@jwt_required
@quser.permissions_required("edit")
def api_activity_counterpart_funding(activity_id):
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
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
            result = qcounterpart_funding.delete_entry(activity_id, request_data["id"])
            if result: return jsonify(result=True)
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
            cf["required_fy"], fq = util.date_to_fy_fq(counterpart_funding.required_date)
            return cf
        counterpart_funding = sorted(
                        list(map(lambda cf: to_fy(cf),
                        qactivity.get_activity(activity_id).counterpart_funding)),
            key=lambda x: x["required_date"])
        return jsonify(counterpart_funding = counterpart_funding,
                       fiscal_years = range(2013,2025))

@blueprint.route("/api/activity_forwardspends/<activity_id>/<fiscal_year>/", methods=["GET", "POST"])
@blueprint.route("/api/activity_forwardspends/<activity_id>/", methods=["GET", "POST"])
@jwt_required
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

@blueprint.route("/api/activity_forwardspends/<activity_id>/update_forwardspends/", methods=['POST'])
@jwt_required
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

@blueprint.route("/api/codelists/update/", methods=["POST"])
@jwt_required
@quser.administrator_required
def api_codelists_update():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.update_attr(request.json)
    else:
        result = qcodelists.update_attr(request.json)
    if result:
        return "OK"
    else:
        return "ERROR"

@blueprint.route("/api/codelists/delete/", methods=["POST"])
@jwt_required
@quser.administrator_required
def api_codelists_delete():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.delete_org(request.json)
    else:
        result = qcodelists.delete_code(request.json)
    if result:
        return "OK"
    else:
        return "ERROR"

@blueprint.route("/api/codelists/new/", methods=["POST"])
@jwt_required
@quser.administrator_required
def api_codelists_new():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.create_organisation(request.json)
    else:
        result = qcodelists.create_code(request.json)
    if result:
        return str(result.id)
    else:
        return "ERROR"

@blueprint.route("/api/")
def api_list_routes():
    return jsonify({
        "iati": url_for("iati.api_list_iati_files", _external=True),
        "csv": url_for("exports.activities_csv", _external=True)
    })


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


@blueprint.route("/api/users.json")
@jwt_required
@quser.permissions_required("edit")
def users():
    _users = quser.user_id_username()
    return jsonify(users=_users)

