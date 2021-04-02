from flask import Blueprint, flash, request, \
    redirect, url_for, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required

from projectdashboard.query import codelists as qcodelists
from projectdashboard.query import activity as qactivity
from projectdashboard.query import location as qlocation
from projectdashboard.query import organisations as qorganisations
from projectdashboard.query import exchangerates as qexchangerates
from projectdashboard.query import milestones as qmilestones
from projectdashboard.query import user as quser
from projectdashboard.lib import codelists
from projectdashboard.lib.codelists import get_codelists
from projectdashboard.views.api import jsonify
from projectdashboard import models

from collections import OrderedDict
import datetime
import difflib


blueprint = Blueprint('activities', __name__, url_prefix='/api/activities')


@blueprint.route("/filters.json")
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
        ("SDG Goals", "sdg-goals", cl["sdg-goals"]),
        ("Activity Status", "activity_status", cl["ActivityStatus"]),
        ("Aid Type", "aid_type", cl["AidType"]),
        ("Domestic / External", "domestic_external", _cl_domestic_external),
        ]
    earliest, latest = qactivity.get_earliest_latest_dates(force=True)
    activity_dates = {
        "earliest": earliest,
        "latest": latest,
    }
    return jsonify(filters=list(map(lambda f: {
        "label": f[0],
        "name": f[1],
        "codes": list(map(lambda fo: fo.as_dict() if type(fo) != dict else fo, f[2])),
        }, filters_codelists)),
        activity_dates=activity_dates
    )


@blueprint.route("/")
@jwt_required(optional=True)
@quser.permissions_required("view")
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
    } for activity in activities]
    )


@blueprint.route("/<activity_id>.json")
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_by_id(activity_id):
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    return jsonify(activity=activity.as_jsonable_dict())


@blueprint.route("/new.json", methods=['GET', 'POST'])
@jwt_required()
@quser.permissions_required("new")
def api_new_activity():
    if request.method=="GET":
        today = datetime.datetime.now().date()
        domestic_external = current_user.permissions_dict.get("edit") or current_user.permissions_dict.get("view")
        if domestic_external == "both":
            domestic_external = "external"
        activity = {
            "title": "",
            "description": "",
            "flow_type": "10",
            "aid_type": "C01",
            "collaboration_type": "1",
            "finance_type": "110",
            "activity_status": "2",
            "tied_status": "5",
            "start_date": today,
            "end_date": today,
            "recipient_country_code": current_user.recipient_country_code,
            "domestic_external": domestic_external,
            "organisations": [ # Here we use the role as the ID so it gets submitted but this is a bad hack
                {
                "role": 1,
                "name": "Funding",
                "entries": [{
                    'percentage': 100,
                    'role': 1,
                    'id': qorganisations.get_organisation_by_name("").id
                    }]
                },
                {
                "role": 4,
                "name": "Implementing",
                "entries": [{
                    'percentage': 100,
                    'role': 4,
                    'id': qorganisations.get_organisation_by_name("").id
                    }]
                }
            ],
            "classifications": {
                "mtef-sector": {
                    "name": "MTEF Sector",
                    "codelist": "mtef-sector",
                    "entries": [{
                        'code': qcodelists.get_code_by_name("mtef-sector", "").id,
                        'percentage': 100,
                        'codelist': 'mtef-sector',
                        'activitycodelist_id': None
                    }]
                },
                "aft-pillar": {
                    "name": "AfT Pillar",
                    "codelist": "aft-pillar",
                    "entries": [{
                        'code': qcodelists.get_code_by_name("aft-pillar", "").id,
                        'percentage': 100,
                        'codelist': 'aft-pillar',
                        'activitycodelist_id': None
                    }]
                },
                "aligned-ministry-agency": {
                    "name": "Aligned Ministry/Agency",
                    "codelist": "aligned-ministry-agency",
                    "entries": [{
                        'code': qcodelists.get_code_by_name("aligned-ministry-agency", "").id,
                        'percentage': 100,
                        'codelist': 'aligned-ministry-agency',
                        'activitycodelist_id': None
                    }]
                },
                "sdg-goals": {
                    "name": "SDG Goals",
                    "codelist": "sdg-goals",
                    "entries": [{
                        'code': qcodelists.get_code_by_name("sdg-goals", "").id,
                        'percentage': 100,
                        'codelist': 'sdg-goals',
                        'activitycodelist_id': None
                    }]
                },
                "papd-pillar": {
                    "name": "PAPD Pillar",
                    "codelist": "papd-pillar",
                    "entries": [{
                        'code': qcodelists.get_code_by_name("papd-pillar", "").id,
                        'percentage': 100,
                        'codelist': 'papd-pillar',
                        'activitycodelist_id': None
                    }]
                }
            },
        }
        return jsonify(activity=activity)
    elif request.method=="POST":
        data = request.get_json()
        if data.get('reporting_org_id') == None:
            return abort(400)
        for codelist, codelist_data in data["classifications"].items():
            data["classification_id_{}".format(codelist)] = codelist_data["entries"][0]["code"]
            data["classification_percentage_{}".format(codelist)] = codelist_data["entries"][0]["percentage"]
        data.pop("classifications")
        for org_role in data["organisations"]:
            data["org_{}".format(org_role["role"])] = org_role["entries"][0]["id"]
        data.pop("organisations")
        data["user_id"] = current_user.id
        a = qactivity.create_activity(data)
        if a:
            return jsonify(a.as_jsonable_dict())
        else:
            return abort(500)


@blueprint.route("/activity_summaries.json", methods=['POST'])
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activity_summaries():
    activity_ids = request.json.get('activity_ids')
    fields = ['id', 'title', 'description', 'objectives', 'deliverables',
        'papd_alignment', 'start_date', 'end_date', 'activity_status']
    fields_special = ['implementing_organisations', 'funding_organisations', #'classifications',
    ]
    fields_len = ['results', 'documents', 'policy_markers', 'locations', 'counterpart_funding'
        ]
    all_fields = fields + fields_special + fields_len

    def get_activity_summary(activity_id):
        activity = qactivity.get_activity(activity_id)
        f = dict([(field, getattr(activity, field)) for field in fields])
        flen = dict([(field, "{} {}".format(len(getattr(activity, field)), field)) for field in fields_len])
        f.update(flen)
        f['implementing_organisations'] = "; ".join(list(map(lambda org: org.name, activity.implementing_organisations)))
        f['funding_organisations'] = "; ".join(list(map(lambda org: org.name, activity.funding_organisations)))
        f['locations'] = "; ".join(list(map(lambda location: location.locations.name, activity.locations)))
        #f['classifications'] = dict(filter(lambda clsf: clsf[0]!='mtef-sector', activity.classification_data_dict.items()))
        return f

    activity_summaries = [get_activity_summary(activity_id) for activity_id in activity_ids]
    all_fields.pop(0) # Delete ID
    # Group results by field
    summaries_by_field = dict([(field, {}) for field in all_fields])
    for activity in activity_summaries:
        for field in all_fields:
            summaries_by_field[field][activity['id']] = activity[field]
    # Get only fields with multiple distinct values
    def filter_unique(field):
        return len(set(list(map(lambda val: str(val), field[1].values()))))>1
    unique_filters = dict(filter(filter_unique, summaries_by_field.items()))
    return jsonify(fields=unique_filters)


@blueprint.route("/finances.json", methods=['POST'])
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_finances():
    activity_ids = request.json.get('activity_ids')
    by_year = request.args.get('by_year')
    activities = [{
        'id': activity_id,
        'finances': OrderedDict(qactivity.get_finances_by_activity_id(activity_id,
        by_year))} for activity_id in activity_ids]
    return jsonify(activities=activities)


@blueprint.route("/<int:activity_id>/finances.json")
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_finances_by_id(activity_id):
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    finances = qactivity.get_finances_by_activity_id(activity_id,
        request.args.get('by_year'))
    return jsonify(
        finances=OrderedDict(finances)
        )

@blueprint.route("/<activity_id>/finances/fund_sources.json")
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_finances_fund_sources_by_id(activity_id):
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)

    commitments = activity.FY_commitments_dict_fund_sources
    allotments = activity.FY_allotments_dict_fund_sources
    disbursements = activity.FY_disbursements_dict_fund_sources
    forwardspends = activity.FY_forward_spend_dict_fund_sources

    finances = list()
    if commitments: finances.append(('commitments', {
        "title": {'external': 'Commitments', 'domestic': 'Appropriations'}[activity.domestic_external],
        "data": commitments
        }))
    if allotments: finances.append(('allotment', {
        "title": 'Allotments',
        "data": allotments
        }))
    if disbursements: finances.append(('disbursement', {
        "title": 'Disbursements',
        "data": disbursements
        }))
    if forwardspends: finances.append(('forwardspend', {
        "title": 'MTEF Projections',
        "data": forwardspends
        }))
    return jsonify(
        finances=OrderedDict(finances),
        fund_sources=activity.disb_fund_sources
    )

def jsonify_results_design(results):
    out = []
    for result in results:
        _result = result.as_dict()
        _result["result_type"] = {
            1: "Output", 2: "Outcome", 3: "Impact"
            }.get(result.result_type)
        if result.indicators:
            _result["indicator_id"] = result.indicators[0].id
            _result["indicator_title"] = result.indicators[0].indicator_title
            _result["measurement_unit_type"] = result.indicators[0].measurement_unit_type
            _result["measurement_type"] = result.indicators[0].measurement_type
            _result["baseline_value"] = result.indicators[0].baseline_value
            if result.indicators[0].baseline_year:
                _result["baseline_year"] = result.indicators[0].baseline_year.year
            _result["periods"] = list(map(lambda p: p.as_dict(), result.indicators[0].periods))
        else:
            _result["periods"] = []
        out.append(_result)
    return out


@blueprint.route("/<activity_id>/results.json")
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_results(activity_id):
    activity = models.Activity.query.get(activity_id)
    if activity == None: return abort(404)
    results = activity.results
    return jsonify(results = jsonify_results_design(results))


@blueprint.route("/<activity_id>/documents.json")
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activities_documents(activity_id):
    activity = models.Activity.query.get(activity_id)
    if activity == None: return abort(404)
    documents = list(map(lambda d: d.as_dict(), activity.documents))
    return jsonify(documents = documents)


@blueprint.route("/<activity_id>/results/data-entry.json", methods=['GET', 'POST'])
@jwt_required()
@quser.permissions_required("results-data-entry")
def api_activities_results_data_entry(activity_id):
    if request.method == "POST":
        result = qactivity.save_results_data_entry(activity_id,
            request.json.get("results"), request.json.get("saveType"))
        if not result: return jsonify(error="Error, could not save data."), 500
    activity = models.Activity.query.get(activity_id)
    if activity == None: return abort(404)
    results = activity.results
    return jsonify(
            activity_id = activity.id,
            activity_title = activity.title,
            results = jsonify_results_design(results)
        )


@blueprint.route("/<activity_id>/results/design.json", methods=['GET', 'POST'])
@jwt_required()
@quser.permissions_required("results-data-design")
def api_activities_results_design(activity_id):
    if request.method == "POST":
        result = qactivity.save_results_data(activity_id, request.json.get("results"))
        if not result: return jsonify(error="Error, could not save data."), 500
    activity = models.Activity.query.get(activity_id)
    if activity == None: return abort(404)
    results = activity.results
    return jsonify(
            activity_id = activity.id,
            activity_title = activity.title,
            results=jsonify_results_design(results)
        )


@blueprint.route("/<activity_id>/delete/", methods=['POST'])
@jwt_required()
def activity_delete(activity_id):
    activity = qactivity.get_activity(activity_id)
    if ((activity.domestic_external=='domestic') and
        ('piu-desk-officer' in current_user.roles_list)) or getattr(current_user, "administrator"):
        result = qactivity.delete_activity(activity_id)
    else:
        abort(403)
    if result:
        return jsonify({'msg': "Successfully deleted that activity"}), 200
    else:
        return jsonify({'msg': "Sorry, unable to delete that activity"}), 500

"""
I think all of this is unused

@blueprint.route("/activities/<activity_id>/edit/update_result/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_edit_result_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = qactivity.update_result_attr(data)
    if update_status == True:
        return "success"
    return "error"

@blueprint.route("/activities/<activity_id>/edit/update_indicator/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_edit_indicator_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = qactivity.update_indicator_attr(data)
    if update_status == True:
        return "success"
    return "error"

@blueprint.route("/activities/<activity_id>/edit/update_period/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_edit_period_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = qactivity.update_indicator_period_attr(data)
    if update_status == True:
        return "success"
    return "error"

@blueprint.route("/activities/<activity_id>/edit/delete_result_data/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_delete_result_data(activity_id):
    data = {
        'id': request.form['id'],
        'result_type': request.form['result_type']
    }
    delete_status = qactivity.delete_result_data(data)
    if delete_status == True:
        return "success"
    return "error"

@blueprint.route("/activities/<activity_id>/edit/add_result_data/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_add_results_data(activity_id):
    data = request.form
    add_status = qactivity.add_result_data(activity_id, data)
    if add_status:
        status_dict = add_status.as_dict()
        for k, v in status_dict.items():
            if k.endswith("year"):
                status_dict[k] = str(v)[0:4]
            if k.startswith("period"):
                status_dict[k] = str(v)[0:10]
        return jsonify(status_dict)
    return "error"
"""


@blueprint.route("/<activity_id>/edit/update_activity/", methods=['POST'])
@jwt_required()
@quser.permissions_required("edit")
def activity_edit_attr(activity_id):
    request_data = request.get_json()
    if request_data['type'] == 'classification':
        activitycodelist_id = request_data['activitycodelist_id']
        update_status = qactivity.update_activity_codelist(
            activitycodelist_id, {"attr": request_data['attr'], "value": request_data['value']}
            )
        if update_status: return "success"
        else: return "error"
    elif request_data['type'] == 'policy_marker':
        policy_marker_code = request_data['code']
        update_status = qactivity.update_activity_policy_marker(
            activity_id,
            int(policy_marker_code),
            {"attr": request_data['attr'], "value": request_data['value']}
            )
        if update_status: return "success"
        else: return "error"
    elif request_data['type'] == 'organisation':
        update_status = qorganisations.update_activity_organisation(
            request_data['activityorganisation_id'],
            request_data['value'])
        if update_status: return "success"
        else: return "error"
    data = {
        'attr': request_data['attr'],
        'value': request_data['value'],
        'id': activity_id,
    }
    update_status = qactivity.update_attr(data)
    if update_status == True:
        return "success"
    return "error"


@blueprint.route("/<activity_id>/milestones/", methods=["GET", "POST"])
@jwt_required(optional=True)
@quser.permissions_required("view")
def api_activity_milestones(activity_id):
    if request.method == "POST":
        request_data = request.get_json()
        milestone_id = request_data["milestone_id"]
        attribute = request_data["attr"]
        value = request_data["value"]
        update_status = qmilestones.add_or_update_activity_milestone({
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


@blueprint.route("/<int:activity_id>/similar/")
@jwt_required(optional=True)
def similar_activities(activity_id):
    return jsonify(
        activities=qactivity.closest_to_activity(activity_id)
    )
