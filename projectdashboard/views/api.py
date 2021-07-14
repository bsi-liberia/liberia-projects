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
    jwt_required
)

from projectdashboard.query import activity as qactivity
from projectdashboard.query import location as qlocation
from projectdashboard.query import finances as qfinances
from projectdashboard.query import exchangerates as qexchangerates
from projectdashboard.query import organisations as qorganisations
from projectdashboard.query import generate_csv as qgenerate_csv
from projectdashboard.query import user as quser
from projectdashboard.query import aggregates as qaggregates

from projectdashboard.lib import util, spreadsheet_headers
from projectdashboard.lib.codelists import get_codelists_lookups, get_codelists
from projectdashboard.lib.util import MONTHS_QUARTERS
from projectdashboard import models
from projectdashboard.extensions import db


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


@blueprint.route("/api/organisations/search_similar/", methods=['POST'])
def search_similar_organisations():
    organisation_name = request.json["organisation_name"]
    similar_organisations = qorganisations.get_similar_organisations(organisation_name)
    return jsonify(
        organisations=similar_organisations
    )

@blueprint.route("/api/user-results/")
@jwt_required()
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


@blueprint.route("/api/codelists.json", methods=["GET", "POST"])
@jwt_required()
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
@jwt_required(optional=True)
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
@jwt_required(optional=True)
def api_sectors_C_D():
    sector_totals = qaggregates.aggregate("mtef-sector")

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
    return jsonify(sectors = list(root.values()))


@blueprint.route("/api/aggregates.json")
@jwt_required(optional=True)
def api_aggregates():
    dimension = request.args.get("dimension")
    if dimension not in ['mtef-sector', 'reporting-org', 'papd-pillar', 'sdg-goals']: abort(405)
    if request.args.get("filter") == 'mtef-sector':
        filter_value = request.args.get("filter-value")
        sector_totals = qaggregates.aggregate(dimension,
            req_filters=[
                models.CodelistCode.codelist_code=='mtef-sector',
                models.CodelistCode.code==filter_value
            ],
            req_finances_joins=[
                models.ActivityFinancesCodelistCode,
                models.CodelistCode
            ],
            req_forwardspends_joins=[
                models.ActivityCodelistCode,
                models.CodelistCode
            ]
        )
    elif request.args.get("filter") == 'reporting-org':
        filter_value = request.args.get("filter-value")
        sector_totals = qaggregates.aggregate(dimension,
            req_filters=[
                models.Activity.reporting_org_id==filter_value
            ],
            req_finances_joins=[
            ],
            req_forwardspends_joins=[
            ]
        )
    else:
        sector_totals = qaggregates.aggregate(dimension)

    def append_path(root, paths):
        if paths:
            sector = root.setdefault("{}_{}_{}".format(paths.domestic_external, paths.fiscal_year, paths.name), {'Commitments': 0.0, 'Disbursements': 0.0, 'Allotments': 0.0, 'Disbursement Projection': 0.0})
            sector[{"C": "Commitments", "D": "Disbursements", "99-A": "Allotments", "FS": "Disbursement Projection"}[paths.transaction_type]] = paths.total_value
            sector["name"] = paths.name
            sector["code"] = str(paths.code)
            sector["domestic_external"] = paths.domestic_external
            sector["fy"] = paths.fiscal_year
    root = {}
    for s in sector_totals: append_path(root, s)
    return jsonify(entries = list(root.values()))
