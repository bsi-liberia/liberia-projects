import datetime
import json
import re
from collections import OrderedDict

from flask import Blueprint, request, \
    url_for, Response, current_app
from flask_login import login_required, current_user
import sqlalchemy as sa
from sqlalchemy.sql import func
import requests

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
from maediprojects.query import import_iati as qimport_iati
from maediprojects.query import monitoring as qmonitoring
from maediprojects.lib import util, spreadsheet_headers
from maediprojects.lib.codelists import get_codelists_lookups, get_codelists
from maediprojects.lib.util import MONTHS_QUARTERS
from maediprojects import models
from maediprojects.extensions import db


blueprint = Blueprint('api', __name__, url_prefix='/', static_folder='../static')


OIPA_SEARCH_URL = "https://www.oipa.nl/api/activities/?format=json&q=%22{}%22&recipient_country=LR&reporting_organisation_identifier={}"

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs), cls=JSONEncoder),
        mimetype='application/json')


@blueprint.route("/api/")
def api():
    return jsonify(
        activities = url_for('api.api_activities_country', _external=True)
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


@blueprint.route("/api/reporting_orgs.json")
@login_required
def reporting_orgs():
    reporting_orgs = qorganisations.get_reporting_orgs()
    ros_fiscal_years = qmonitoring.forwardspends_ros("current")
    ros_fiscal_years_previous = qmonitoring.forwardspends_ros("previous")
    ros_disbursements = qmonitoring.fydata_ros("todate")
    def annotate_ro(ro):
        _ro = ro.as_dict()
        _ro["activities_count"] = ro.activities_count
        _ro["forwardspends"] = {
            "current": ros_fiscal_years.get(ro.id, 0.00),
            "previous": ros_fiscal_years_previous.get(ro.id, 0.00)
        }
        _ro["disbursements"] = {
            "Q1": ros_disbursements.get((ro.id, u"Q1"), 0.00),
            "Q2": ros_disbursements.get((ro.id, u"Q2"), 0.00),
            "Q3": ros_disbursements.get((ro.id, u"Q3"), 0.00),
            "Q4": ros_disbursements.get((ro.id, u"Q4"), 0.00)
        }
        return _ro

    return jsonify(
        orgs=list(map(lambda ro: annotate_ro(ro), reporting_orgs)),
        current_year = util.FY("current").fy_fy(),
        previous_year = util.FY("previous").fy_fy(),
        list_of_quarters = util.Last4Quarters().list_of_quarters()
        )


@blueprint.route("/api/reporting_orgs/summary.json")
@login_required
def reporting_orgs_summary():
    reporting_orgs = qorganisations.get_reporting_orgs()
    ros_fiscal_years = qmonitoring.forwardspends_ros("current")
    ros_fiscal_years_previous = qmonitoring.forwardspends_ros("previous")
    ros_disbursements = qmonitoring.fydata_ros("todate")
    def annotate_ro(ro):
        _ro = ro.as_dict()
        _ro["activities_count"] = ro.activities_count
        _ro["forwardspends"] = {
            "current": ros_fiscal_years.get(ro.id, 0.00),
            "previous": ros_fiscal_years_previous.get(ro.id, 0.00)
        }
        _ro["disbursements"] = {
            "Q1": ros_disbursements.get((ro.id, u"Q1"), 0.00),
            "Q2": ros_disbursements.get((ro.id, u"Q2"), 0.00),
            "Q3": ros_disbursements.get((ro.id, u"Q3"), 0.00),
            "Q4": ros_disbursements.get((ro.id, u"Q4"), 0.00)
        }
        return _ro

    orgs = list(map(lambda ro: annotate_ro(ro), reporting_orgs))

    def generate_summary(list_of_quarters, orgs):
        out = dict(map(lambda q: (q, { True: 0, False: 0, "Total": 0 }), list_of_quarters.keys()))
        for ro in orgs:
            for disb_q, disb_v in ro["disbursements"].items():
                out[disb_q][disb_v>0] += 1
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


@blueprint.route("/api/activities/filters.json")
def api_activities_filters():
    reporting_orgs = qorganisations.get_reporting_orgs()
    organisation_types = qorganisations.get_organisation_types()
    cl = get_codelists()
    _cl_domestic_external = [
        {"id": "domestic",
         "name": "Domestic (PSIP / PIU)"},
        {"id": "external",
         "name": "External (Aid / AMCU)"}
    ]
    filters_codelists = [
        ("Reported by", "reporting_org_id", reporting_orgs),
        ("Type of Implementer", "implementing_org_type", organisation_types),
        ("Sector", "mtef-sector", cl["mtef-sector"]),
        ("Aligned Ministry / Agency", "aligned-ministry-agency", cl["aligned-ministry-agency"]),
        ("PAPD Pillar", "papd-pillar", cl["papd-pillar"]),
        ("Activity Status", "activity_status", cl["ActivityStatus"]),
        ("Aid Type", "aid_type", cl["AidType"]),
        ("Domestic / External", "domestic_external", _cl_domestic_external),
        ]
    return jsonify(filters=list(map(lambda f: {
        "label": f[0],
        "name": f[1],
        "codes": list(map(lambda fo: fo.as_dict() if type(fo) != dict else fo, f[2])),
        }, filters_codelists)))


@blueprint.route("/api/activities/")
def api_activities_country():
    arguments = request.args.to_dict()
    activities = qactivity.list_activities_by_filters(arguments)
    activity_commitments, activity_disbursements, activity_projected_disbursements = qactivity.activity_C_D_FSs()
    def round_or_zero(value):
        if not value: return 0
        return round(value)
    def make_pct(value1, value2):
        if value2 == 0: return None
        return (value1/value2)*100
    return jsonify(activities = [{
        'title': activity.title,
        'reporting_org': activity.reporting_org.name,
        'id': activity.id,
        'updated_date': activity.updated_date.date().isoformat(),
        'total_commitments': round_or_zero(activity_commitments.get(activity.id)),
        'total_disbursements': round_or_zero(activity_disbursements.get(activity.id)),
        'total_projected_disbursements': round_or_zero(activity_projected_disbursements.get(activity.id)),
        'pct_disbursements_projected': make_pct(activity_disbursements.get(activity.id, 0), activity_projected_disbursements.get(activity.id, 0)),
        'pct_disbursements_committed': make_pct(activity_disbursements.get(activity.id, 0), activity_commitments.get(activity.id, 0)),
        'user': activity.user.username,
        'user_id': activity.user.id,
        "permissions": activity.permissions
    } for activity in activities])

@blueprint.route("/api/activities/<activity_id>.json")
def api_activities_by_id(activity_id):
    cl_lookups = get_codelists_lookups()
    activity = qactivity.get_activity(activity_id)
    data = qgenerate_csv.activity_to_json(activity, cl_lookups)

    return jsonify(data)

@blueprint.route("/api/activities/complete/<activity_id>.json")
def api_activities_by_id_complete(activity_id):
    cl_lookups = get_codelists_lookups()
    activity = qactivity.get_activity(activity_id).as_jsonable_dict()

    return jsonify(activity)

@blueprint.route("/api/api_activity_milestones/<activity_id>/", methods=["POST"])
@login_required
@quser.permissions_required("view")
def api_activity_milestones(activity_id):
    milestone_id = request.form["milestone_id"]
    attribute = request.form["attribute"]
    value = request.form["value"]
    if attribute == "achieved": value={"true": True, "false": False}[value]
    update_status = qmilestone.add_or_update_activity_milestone({
                "activity_id": activity_id,
                "milestone_id": milestone_id,
                "attribute": attribute,
                "value": value})
    if update_status == True:
        return "success"
    return "error"

@blueprint.route("/api/activity_finances/<activity_id>/", methods=["POST", "GET"])
@login_required
@quser.permissions_required("edit")
def api_activity_finances(activity_id):
    """GET returns a list of all financial data for a given activity_id.
    POST also accepts financial data to be added or deleted."""
    if request.method == "POST":
        if request.form["action"] == "add":
            data = {
                "transaction_type": request.form["transaction_type"],
                "transaction_date": request.form["transaction_date"],
                "transaction_value": request.form["transaction_value"],
                "aid_type": request.form["aid_type"],
                "finance_type": request.form["finance_type"],
                "provider_org_id": request.form["provider_org_id"],
                "receiver_org_id": request.form["receiver_org_id"],
                "currency": request.form.get("currency", u"USD"),
                "classifications": {
                    "mtef-sector": request.form["mtef_sector"]
                }
            }
            result = jsonify(qfinances.add_finances(activity_id, data).as_dict())
        elif request.form["action"] == "delete":
            result = str(qfinances.delete_finances(activity_id, request.form["transaction_id"]))
        return result
    elif request.method == "GET":
        finances = list(map(lambda transaction: transaction.as_dict(),
                         qactivity.get_activity(activity_id).finances))
        return jsonify(finances = finances)

@blueprint.route("/api/activity_finances/<activity_id>/update_finances/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def finances_edit_attr(activity_id):
    data = {
        'activity_id': activity_id,
        'attr': request.form['attr'],
        'value': request.form['value'],
        'finances_id': request.form['finances_id'],
    }

    #Run currency conversion if:
    # we now set to automatic
    # we change the currency and have set to automatic
    if (data.get("attr") == "currency_automatic") and (data.get("value") == "1"):
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
        return jsonify(update_status.as_dict())
    elif data["attr"] == "mtef_sector":
        data["attr"] = 'mtef-sector' #FIXME make consistent
        update_status = qfinances.update_finances_classification(data)
    else:
        update_status = qfinances.update_attr(data)
    if update_status:
        return jsonify(update_status.as_dict())
    return "error"

@blueprint.route("/api/activity_counterpart_funding/<activity_id>/", methods=["POST", "GET"])
@login_required
@quser.permissions_required("edit")
def api_activity_counterpart_funding(activity_id):
    """GET returns a list of all counterpart funding for a given activity_id.
    POST also accepts counterpart funding data to be added, deleted, updated."""
    if request.method == "POST":
        if request.form["action"] == "add":
            required_date = util.fq_fy_to_date(1,
                int(request.form["required_fy"])).date().isoformat()
            data = {
                "required_value": request.form["required_value"],
                "required_date": required_date,
                "budgeted": False,
                "allotted": False,
                "disbursed": False,
            }
            result = qcounterpart_funding.add_entry(activity_id, data)
        elif request.form["action"] == "delete":
            result = qcounterpart_funding.delete_entry(activity_id, request.form["id"])
        elif request.form["action"] == "update":
            attr = request.form['attr']
            value = request.form['value']
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
                'id': request.form['id'],
            }
            update_status = qcounterpart_funding.update_entry(data)
            if update_status == True:
                return "success"
            return "error"
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
@login_required
@quser.permissions_required("edit")
def api_activity_forwardspends(activity_id, fiscal_year=True):
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
        if request.form["value"] in (None, " ", ""):
            value = 0
        else:
            value = request.form["value"]
        data = {
            "id": request.form["id"],
            "value": value
        }
        update_status = qfinances.update_fs_attr(data)
        if update_status == True:
            return "success"
        return "error"

@blueprint.route("/api/activity_forwardspends/<activity_id>/update_forwardspends/", methods=['POST'])
@login_required
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
@login_required
def api_all_activity_locations():
    """GET returns a list of all locations."""
    query = models.ActivityLocation.query.join(models.Activity)
    query = qactivity.filter_activities_for_permissions(query)
    activitylocations = query.all()
    locations = list(map(lambda al: ({"locations": al.locations.as_dict(),
        "title": al.activity.title,
        "id": al.activity_id,
        "url": url_for('activities.activity', activity_id=al.activity_id,
            _external=True)}),
        activitylocations))
    return jsonify(locations = locations)

@blueprint.route("/api/activity_locations/<activity_id>/", methods=["POST", "GET"])
@login_required
@quser.permissions_required("edit")
def api_activity_locations(activity_id):
    """GET returns a list of all locations for a given activity_id.
    POST also accepts locations to be added or deleted."""
    if request.method == "POST":
        if request.form["action"] == "add":
            result = qlocation.add_location(activity_id, request.form["location_id"])
        elif request.form["action"] == "delete":
            result = qlocation.delete_location(activity_id, request.form["location_id"])
        return str(result)
    elif request.method == "GET":
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
@login_required
@quser.administrator_required
def api_codelists_update():
    # FIXME check for admin status
    if request.form["codelist_code"] == "organisation":
        result = qorganisations.update_attr(request.form)
    else:
        result = qcodelists.update_attr(request.form)
    if result:
        return "OK"
    else:
        return "ERROR"

@blueprint.route("/api/codelists/delete/", methods=["POST"])
@login_required
@quser.administrator_required
def api_codelists_delete():
    # FIXME check for admin status
    if request.form["codelist_code"] == "organisation":
        result = qorganisations.delete_org(request.form)
    else:
        result = qcodelists.delete_code(request.form)
    if result:
        return "OK"
    else:
        return "ERROR"

@blueprint.route("/api/codelists/new/", methods=["POST"])
@login_required
@quser.administrator_required
def api_codelists_new():
    # FIXME check for admin status
    if request.form["codelist_code"] == "organisation":
        result = qorganisations.create_organisation(request.form)
    else:
        result = qcodelists.create_code(request.form)
    if result:
        return str(result.id)
    else:
        return "ERROR"

@blueprint.route("/api/")
def api_list_routes():
    return jsonify({
        "iati": url_for("api.api_list_iati_files", _external=True),
        "csv": url_for("exports.activities_csv", _external=True)
    })

@blueprint.route("/api/iati.json")
def api_list_iati_files():
    urls = qactivity.get_iati_list()
    return jsonify(urls = urls)

@blueprint.route("/api/iati_search/")
def api_iati_search():
    title = request.args["title"]
    reporting_org_code = re.sub(r"\|", ",", request.args["reporting_org_code"]) # For OR, OIPA uses , rather than |
    r = requests.get(OIPA_SEARCH_URL.format(title.encode("utf-8"), reporting_org_code))
    data = json.loads(r.text)
    return jsonify(data)


@blueprint.route("/api/iati_fetch_data/<activity_id>/")
@login_required
@quser.permissions_required("edit")
def api_iati_fetch_data(activity_id):
    iati_identifier = request.args["iati_identifier"]
    iati_document_result = qimport_iati.import_documents(activity_id, iati_identifier)
    return str(iati_document_result)


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
        models.CodelistCode.name != u""
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
        models.CodelistCode.name != u""
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
    return jsonify(sectors = root.values())

@blueprint.route("/api/iati/<version>/<country_code>.xml")
def generate_iati_xml(version, country_code):
    if version == "1.03":
        xml = qgenerate.generate_103(country_code)
        return Response(xml, mimetype='text/xml')
    elif version == "2.01":
        xml = qgenerate.generate_201(country_code)
        return Response(xml, mimetype='text/xml')

    return "ERROR: UNKNOWN VERSION"


@blueprint.route("/api/activitylog.json")
@login_required
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
                "username": al.user.username,
                "url": url_for("users.users_edit", user_id=al.id, _external=True)
            },
            "activity": {
                "id": al.activity_id,
                "title": al.activity.title,
                "url": url_for("activities.activity", activity_id=al.activity_id, _external=True)
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
@login_required
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
            "username": al.user.username,
            "url": url_for("users.users_edit", user_id=al.id, _external=True)
        },
        "activity": {
            "id": al.activity_id,
            "title": al.activity.title,
            "url": url_for("activities.activity", activity_id=al.activity_id, _external=True)
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
@login_required
@quser.permissions_required("edit")
def users():
    _users = quser.user_id_username()
    return jsonify(users=_users)

