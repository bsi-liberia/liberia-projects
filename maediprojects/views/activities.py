import datetime

from flask import Blueprint, render_template, flash, request, \
    redirect, url_for, abort, jsonify
from flask_login import login_required, current_user

from maediprojects.query import codelists as qcodelists
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import organisations as qorganisations
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import user as quser
from maediprojects.lib import codelists


blueprint = Blueprint('activities', __name__, url_prefix='/', static_folder='../static')

@blueprint.route("/")
@login_required
def dashboard():
    countries = qactivity.get_iati_list()
    reporting_orgs = qorganisations.get_organisations()
    mtef_sectors = codelists.get_codelists_lookups_by_name()["mtef-sector"]
    aligned_ministry_agencies = codelists.get_codelists_lookups_by_name()["aligned-ministry-agency"]
    return render_template("home.html",
                countries=countries,
                reporting_orgs=reporting_orgs,
                mtef_sectors=sorted(mtef_sectors.items()),
                aligned_ministry_agencies=sorted(aligned_ministry_agencies.items()),
                loggedinuser=current_user,
                stats = qactivity.get_stats(current_user)
                          )

@blueprint.route("/activities/")
@login_required
def activities():
    reporting_orgs = qorganisations.get_reporting_orgs()
    organisation_types = qorganisations.get_organisation_types()
    cl = codelists.get_codelists()
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
    activity_base_url = url_for("activities.activities", _external=True)
    earliest, latest = qactivity.get_earliest_latest_dates()
    if (earliest == latest) and (earliest != None):
        latest += datetime.timedelta(days=1)
    dates = {
        "earliest": earliest.isoformat() if earliest else "{}-01-01".format(datetime.datetime.now().year),
        "latest": latest.isoformat() if latest else "{}-12-31".format(datetime.datetime.now().year),
    }
    return render_template("activities.html",
                reporting_orgs=reporting_orgs,
                codelists=filters_codelists,
                loggedinuser=current_user,
                activity_base_url = activity_base_url,
                dates=dates
    )

@blueprint.route("/activities/new/", methods=['GET', 'POST'])
@login_required
@quser.permissions_required("edit")
def activity_new():
    if request.method == "GET":
        today = datetime.datetime.now().date().isoformat()
        return render_template("activity_edit.html",
            # Specify some defaults
            activity = {
                "flow_type": "10",
                "aid_type": "C01",
                "collaboration_type": "1",
                "finance_type": "110",
                "activity_status": "2",
                "tied_status": "5",
                "start_date": today,
                "end_date": today,
                "recipient_country_code": current_user.recipient_country_code,
                "domestic_external": current_user.permissions_dict.get("domestic_external_edit"),
                "organisations": [ # Here we use the role as the ID so it gets submitted but this is a bad hack
                    {"role": 1, "id": 1, "organisation": { "id": ""}},
                    {"role": 4, "id": 4, "organisation": { "id": ""}}
                ],
                "classification_data": {
                    "mtef-sector": {
                        "name": "MTEF Sector",
                        "code": "mtef-sector",
                        "id": "mtef-sector",
                        "entries": [
                            {""}
                        ]
                    },
                    "aft-pillar": {
                        "name": "AfT Pillar",
                        "code": "aft-pillar",
                        "id": "aft-pillar",
                        "entries": [
                            {""}
                        ]
                    },
                    "aligned-ministry-agency": {
                        "name": "Aligned Ministry/Agency",
                        "code": "aligned-ministry-agency",
                        "id": "aligned-ministry-agency",
                        "entries": [
                            {""}
                        ]
                    },
                    "sdg-goals": {
                        "name": "SDG Goals",
                        "code": "sdg-goals",
                        "id": "sdg-goals",
                        "entries": [
                            {""}
                        ]
                    },
                    "papd-pillar": {
                        "name": "PAPD Pillar",
                        "code": "papd-pillar",
                        "id": "papd-pillar",
                        "entries": [
                            {""}
                        ]
                    }
                },
            },
            loggedinuser=current_user,
            organisations = qorganisations.get_organisations(),
            codelists = codelists.get_codelists(),
            users = quser.user()
            )

    elif request.method == "POST":
        # Create new activity
        data = request.form.to_dict()
        data["user_id"] = current_user.id
        a = qactivity.create_activity(data)
        if a:
            flash("Successfully added your activity", "success")
        else:
            flash("An error occurred and your activity couldn't be added", "danger")
        return redirect(url_for('activities.activity_edit', activity_id=a.id))

@blueprint.route("/activities/<activity_id>/delete/")
@login_required
@quser.permissions_required("edit")
def activity_delete(activity_id):
    result = qactivity.delete_activity(activity_id)
    if result:
        flash("Successfully deleted that activity", "success")
    else:
        flash("Sorry, unable to delete that activity", "danger")
    return redirect(url_for("activities.activities"))


@blueprint.route("/activities/<activity_id>/")
@login_required
@quser.permissions_required("view")
def activity(activity_id):
    activity = qactivity.get_activity(activity_id)
    if not activity:
        return(abort(404))
    locations = qlocation.get_locations_country(
                                    activity.recipient_country_code)
    return render_template(
        "activity.html",
        activity=activity,
        loggedinuser=current_user,
        codelists=codelists.get_codelists(),
        codelist_lookups=codelists.get_codelists_lookups(),
        locations=locations,
        api_locations_url=url_for("api.api_locations", country_code=activity.recipient_country_code),
        api_activity_locations_url=url_for("api.api_activity_locations", activity_id=activity_id),
        api_activity_finances_url=url_for("api.api_activity_finances", activity_id=activity_id),
        api_update_activity_finances_url=url_for("api.finances_edit_attr", activity_id=activity_id),
        api_iati_search_url=url_for("api.api_iati_search"),
        api_activity_forwardspends_url=url_for("api.api_activity_forwardspends", activity_id=activity_id),
        users=quser.user()
    )


@blueprint.route("/activities/<activity_id>/edit/")
@login_required
@quser.permissions_required("edit")
def activity_edit(activity_id):
    activity = qactivity.get_activity(activity_id)
    locations = qlocation.get_locations_country(
                                    activity.recipient_country_code)
    return render_template(
        "activity_edit.html",
        activity=activity,
        loggedinuser=current_user,
        codelists=codelists.get_codelists(),
        codelist_lookups=codelists.get_codelists_lookups(),
        organisations=qorganisations.get_organisations(),
        locations=locations,
        currencies = qexchangerates.get_currencies(),
        api_locations_url=url_for("api.api_locations", country_code=activity.recipient_country_code),
        api_activity_locations_url=url_for("api.api_activity_locations", activity_id=activity_id),
        api_activity_finances_url=url_for("api.api_activity_finances", activity_id=activity_id),
        api_activity_milestones_url=url_for("api.api_activity_milestones", activity_id=activity_id),
        api_update_activity_finances_url=url_for("api.finances_edit_attr", activity_id=activity_id),
        api_iati_search_url=url_for("api.api_iati_search"),
        api_iati_fetch_data_url = url_for("api.api_iati_fetch_data", activity_id=activity_id),
        api_activity_forwardspends_url=url_for("api.api_activity_forwardspends", activity_id=activity_id),
        api_activity_counterpart_funding_url = url_for("api.api_activity_counterpart_funding", activity_id=activity_id),
        users=quser.user()
    )


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


@blueprint.route("/activities/<activity_id>/edit/update_activity/", methods=['POST'])
@login_required
@quser.permissions_required("edit")
def activity_edit_attr(activity_id):
    #FIXME this is a bit hacky
    if request.form['attr'].startswith("classification_"):
        if request.form['attr'].startswith("classification_id"):
            activitycodelist_id = request.form['attr'].split("classification_id_")[1]
            attr = "codelist_code_id"
        if request.form['attr'].startswith("classification_percentage"):
            activitycodelist_id = request.form['attr'].split("classification_percentage_")[1]
            attr = "percentage"
        update_status = qcodelists.update_activity_codelist(
            activitycodelist_id, {"attr": attr, "value": request.form['value']}
            )
        if update_status: return "success"
        else: return "error"
    if request.form['attr'].startswith("org"):
        update_status = qorganisations.update_activity_organisation(
            request.form['attr'].split("_")[1],
            request.form['value'])
        if update_status: return "success"
        else: return "error"
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': activity_id,
    }
    update_status = qactivity.update_attr(data)
    if update_status == True:
        return "success"
    return "error"