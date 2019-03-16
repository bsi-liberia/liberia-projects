import datetime

from flask import Blueprint, render_template, flash, request, \
    redirect, url_for, abort, jsonify
from flask_login import login_required, current_user

from maediprojects.query import codelists as qcodelists
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import organisations as qorganisations
from maediprojects.query import generate_xlsx as qgenerate_xlsx
from maediprojects.query import user as quser
from maediprojects.lib import codelists, util


blueprint = Blueprint('activities', __name__, url_prefix='/', static_folder='../static')


ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    countries = qactivity.get_iati_list()
    reporting_orgs = list(map(lambda o: {"id": o.id, "name": o.name}, qorganisations.get_reporting_orgs()))
    cl = codelists.get_codelists()
    _cl_domestic_external = [
        {"id": "domestic",
         "name": "Domestic (PSIP / PIU)"},
        {"id": "external",
         "name": "External (Aid / AMCU)"}
    ]
    filters_codelists = [
        ("Reported by", "reporting_org_id", reporting_orgs),
        ("Sector", "mtef-sector", cl["mtef-sector"]),
        ("Aligned Ministry / Agency", "aligned-ministry-agency", cl["aligned-ministry-agency"]),
        ("PAPD Pillar", "papd-pillar", cl["papd-pillar"]),
        ("Activity Status", "activity_status", cl["ActivityStatus"]),
        ("Aid Type", "aid_type", cl["AidType"]),
        ("Domestic / External", "domestic_external", _cl_domestic_external),
        ]
    activity_base_url = url_for("activities.activities")
    earliest, latest = qactivity.get_earliest_latest_dates()
    dates = {
        "earliest": earliest.isoformat(),
        "latest": latest.isoformat()
    }
    return render_template("activities.html",
                countries=countries,
                reporting_orgs=reporting_orgs,
                codelists=filters_codelists,
                loggedinuser=current_user,
                stats = qactivity.get_stats(current_user),
                activity_base_url = activity_base_url,
                dates=dates
    )

@blueprint.route("/export/")
def export():
    reporting_orgs = qorganisations.get_reporting_orgs()
    available_fys_fqs = util.available_fy_fqs_as_dict()
    previous_fy_fq = util.column_data_to_string(util.previous_fy_fq())
    return render_template("export.html",
                loggedinuser = current_user,
                funding_orgs=reporting_orgs,
                previous_fy_fq = previous_fy_fq,
                available_fys_fqs = available_fys_fqs)

@blueprint.route("/import/", methods=["POST", "GET"])
@login_required
def import_template():
    if request.method == "GET": return(redirect(url_for('activities.export')))
    if 'file' not in request.files:
        flash('Please select a file.', "warning")
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Please select a file.', "warning")
        return redirect(request.url)
    if file and allowed_file(file.filename):
        fy_fq = request.form['fy_fq']
        # For each sheet: convert to dict
        # For each line in each sheet:
        # Process (financial data) import column
        # If no data in that FQ: then import
        # If there was data for that FY: then don't import
        result = qgenerate_xlsx.import_xls(file, fy_fq)
        if result > 0: flash("{} activities successfully updated!".format(result), "success")
        else: flash("""No activities were updated. No updated disbursements
        were found. Check that you selected the correct file and that it
        contains {} data. It must be formatted according to
        the AMCU template format. You can download a copy of this template
        below.""".format(util.column_data_to_string(fy_fq)), "warning")
        return redirect(url_for('activities.export'))
    flash("Sorry, there was an error, and that file could not be imported", "danger")
    return redirect(url_for('activities.export'))

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
    if not activity: return(abort(404))
    locations = qlocation.get_locations_country(
                                    activity.recipient_country_code)
    #FIXME why are these not url_for()s ?
    return render_template("activity.html",
                activity = activity,
                loggedinuser=current_user,
                codelists = codelists.get_codelists(),
                codelist_lookups = codelists.get_codelists_lookups(),
                locations = locations,
                api_locations_url ="/api/locations/%s/" % activity.recipient_country_code,
                api_activity_locations_url = "/api/activity_locations/%s/" % activity_id,
                api_activity_finances_url = "/api/activity_finances/%s/" % activity_id,
                api_update_activity_finances_url = "/api/activity_finances/%s/update_finances/" % activity_id,
                api_iati_search_url = "/api/iati_search/",
                api_activity_forwardspends_url = url_for("api.api_activity_forwardspends", activity_id=activity_id),
                users = quser.user()
          )

@blueprint.route("/activities/<activity_id>/edit/")
@login_required
@quser.permissions_required("edit")
def activity_edit(activity_id):
    activity = qactivity.get_activity(activity_id)
    locations = qlocation.get_locations_country(
                                    activity.recipient_country_code)
    #FIXME why are these not url_for()s ?
    return render_template("activity_edit.html",
                activity = activity,
                loggedinuser=current_user,
                codelists = codelists.get_codelists(),
                organisations = qorganisations.get_organisations(),
                locations = locations,
                api_locations_url ="/api/locations/%s/" % activity.recipient_country_code,
                api_activity_locations_url = "/api/activity_locations/%s/" % activity_id,
                api_activity_finances_url = "/api/activity_finances/%s/" % activity_id,
                api_activity_milestones_url = url_for("api.api_activity_milestones", activity_id=activity_id),
                api_update_activity_finances_url = "/api/activity_finances/%s/update_finances/" % activity_id,
                api_iati_search_url = "/api/iati_search/",
                api_activity_forwardspends_url = url_for("api.api_activity_forwardspends", activity_id=activity_id),
                users = quser.user()
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