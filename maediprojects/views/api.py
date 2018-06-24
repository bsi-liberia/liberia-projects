from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, \
    jsonify, current_app
from flask.ext.login import login_required, current_user
from sqlalchemy.sql import func
                            
from maediprojects import app, db, models
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import finances as qfinances
from maediprojects.query import codelists as qcodelists
from maediprojects.query import generate as qgenerate
from maediprojects.query import generate_csv as qgenerate_csv
from maediprojects.query import generate_xlsx as qgenerate_xlsx
from maediprojects.lib import codelists
from maediprojects.lib.util import MONTHS_QUARTERS, QUARTERS_MONTH_DAY
import requests
import datetime, json, collections
from dateutil.relativedelta import relativedelta

OIPA_SEARCH_URL = "https://www.oipa.nl/api/activities/?format=json&q=%22{}%22&recipient_country=LR&reporting_organisation_identifier={}"

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
            indent=None if request.is_xhr else 2, cls=JSONEncoder),
        mimetype='application/json')

@app.route("/api/activities/", methods=["POST", "GET"])
def api_activities_country():
    if "country_code" in request.form:
        activities = qactivity.list_activities_by_country(
            request.form["country_code"])
    elif "funding_org_code" in request.form:
        activities = qactivity.list_activities_by_filter(
            "funding_org_code",
            request.form["funding_org_code"])
    elif "mtef_sector" in request.form:
        activities = qactivity.list_activities_by_filter(
            "mtef-sector",
            request.form["mtef_sector"])
    elif "aligned_ministry_agency" in request.form:
        activities = qactivity.list_activities_by_filter(
            "aligned-ministry-agency",
            request.form["aligned_ministry_agency"])
    else:
        activities = qactivity.list_activities_user(current_user)

    return jsonify(activities = [{
        'title': activity.title,
        'country': activity.recipient_country.name,
        'funding_org': activity.funding_org.name,
        'id': activity.id,
        'updated_date': activity.updated_date.date().isoformat(),
        'activity_edit_url': url_for('activity_edit', 
              activity_id = activity.id),
        'activity_delete_url': url_for('activity_delete', 
              activity_id = activity.id),
        'user': activity.user.username,
        'user_id': activity.user.id,
    } for activity in activities])

@app.route("/api/activity_finances/<activity_id>/", methods=["POST", "GET"])
@login_required
def api_activity_finances(activity_id):
    """GET returns a list of all financial data for a given activity_id. 
    
    POST also accepts financial data to be added or deleted."""
    
    if request.method == "POST":
        if request.form["action"] == "add":
            data = {
                "transaction_type": request.form["transaction_type"]
            }
            result = qfinances.add_finances(activity_id, data)
        elif request.form["action"] == "delete":
            result = qfinances.delete_finances(activity_id, request.form["transaction_id"])
        return str(result)
    elif request.method == "GET":
        finances = list(map(lambda x: x.as_dict(), 
                         qactivity.get_activity(activity_id).finances))
        return jsonify(finances = finances)

@app.route("/api/activity_finances/<activity_id>/update_finances/", methods=['POST'])
@login_required
def finances_edit_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'finances_id': request.form['finances_id'],
    }
    update_status = qfinances.update_attr(data)
    if update_status == True:
        return "success"
    return "error"

@app.route("/api/activity_forwardspends/<activity_id>/", methods=["GET", "POST"])
@login_required
def api_activity_forwardspends(activity_id):
    """GET returns a list of all forward spend data for a given activity_id.
    
    POST updates value for a given forwardspend_id."""

    if request.method == "GET":
        data = qactivity.get_activity(activity_id).forwardspends
        forwardspends = list(map(lambda fs_db: fs_db.as_dict(),
                         qactivity.get_activity(activity_id).forwardspends))
        years = sorted(set(map(lambda fs: fs["value_date"].year, 
                         forwardspends)))
        out = collections.OrderedDict()
        for year in years:
            out[year] = {"year": year, "total_value": 0.00}
            for forwardspend in forwardspends:
                if forwardspend["period_start_date"].year == year:
                    fq = MONTHS_QUARTERS[forwardspend["period_start_date"].month]
                    out[year]["Q{}".format(fq)] = forwardspend
                    out[year]["total_value"] += float(forwardspend["value"])
        out = list(out.values())
        return jsonify(forwardspends=out)

    elif request.method == "POST":

        data = {
            "id": request.form["id"],
            "value": request.form["value"]
        }
        update_status = qfinances.update_fs_attr(data)
        if update_status == True:
            return "success"
        return "error"

@app.route("/api/activity_forwardspends/<activity_id>/update_forwardspends/", methods=['POST'])
@login_required
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

@app.route("/api/activity_locations/<activity_id>/", methods=["POST", "GET"])
@login_required
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

@app.route("/api/locations/<country_code>/")
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

@app.route("/api/codelists/update/", methods=["POST"])
@login_required
def api_codelists_update():
    # FIXME check for admin status
    result = qcodelists.update_attr(request.form)
    if result:
        return "OK"
    else:
        return "ERROR"

@app.route("/api/codelists/delete/", methods=["POST"])
@login_required
def api_codelists_delete():
    # FIXME check for admin status
    result = qcodelists.delete_code(request.form)
    if result:
        return "OK"
    else:
        return "ERROR"

@app.route("/api/codelists/new/", methods=["POST"])
@login_required
def api_codelists_new():
    # FIXME check for admin status
    result = qcodelists.create_code(request.form)
    if result:
        return "OK"
    else:
        return "ERROR"

@app.route("/api/")
def api_list_routes():
    return jsonify({
        "iati": url_for("api_list_iati_files"),
        "csv": url_for("maedi_activities_csv")
    })

@app.route("/api/iati.json")
def api_list_iati_files():
    urls = qactivity.get_iati_list()
    return jsonify(urls = urls)

@app.route("/api/iati_search/", methods=["POST"])
def api_iati_search():
    title = request.form["title"]
    reporting_org_code = request.form["reporting_org_code"]
    
    r = requests.get(OIPA_SEARCH_URL.format(title, reporting_org_code))
    data = json.loads(r.text)
    return jsonify(data)

@app.route("/api/sectors.json", methods=["GET", "POST"])
def api_sectors():
    sector_totals = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("total_disbursement"),
        models.CodelistCode.code,
        models.CodelistCode.name,
        func.strftime('%Y', func.date(models.ActivityFinances.transaction_date, 'start of month', '-6 month')).label("fiscal_year")
    ).join(
        models.Activity,
        models.ActivityCodelistCode,
        models.CodelistCode
    ).filter(
        models.ActivityFinances.transaction_type == "D",
        models.CodelistCode.codelist_code == "mtef-sector"
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

@app.route("/api/iati/<version>/<country_code>.xml")
def generate_iati_xml(version, country_code):
    if version == "1.03":
        xml = qgenerate.generate_103(country_code)
        return Response(xml, mimetype='text/xml')
    elif version == "2.01":
        xml = qgenerate.generate_201(country_code)
        return Response(xml, mimetype='text/xml')

    return "ERROR: UNKNOWN VERSION"

@app.route("/api/activities.csv")
def maedi_activities_csv():
    data = qgenerate_csv.generate_csv()
    data.seek(0)
    return Response(data, mimetype="text/csv")

@app.route("/api/activities.xlsx")
def maedi_activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx()
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
