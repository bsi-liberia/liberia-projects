from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, \
    jsonify, current_app
from flask.ext.login import login_required, current_user
                            
from maediprojects import app, db, models
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import finances as qfinances
from maediprojects.query import codelists as qcodelists
from maediprojects.query import generate as qgenerate
from maediprojects.lib import codelists
import datetime, json

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
    if "country_code" not in request.form:
        activities = qactivity.list_activities_user(current_user)
    else:
        activities = qactivity.list_activities_by_country(
            request.form["country_code"])

    return jsonify(activities = [{
        'title': activity.title,
        'country': activity.recipient_country.name,
        'id': activity.id,
        'updated_date': activity.updated_date.date().isoformat(),
        'activity_edit_url': url_for('activity_edit', 
              activity_id = activity.id),
        'activity_delete_url': url_for('activity_delete', 
              activity_id = activity.id)
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

@app.route("/api/iati.json")
def api_list_iati_files():
    urls = qactivity.get_iati_list()
    return jsonify(urls = urls)

@app.route("/api/iati/<version>/<country_code>.xml")
def generate_iati_xml(version, country_code):
    if version == "1.03":
        xml = qgenerate.generate_103(country_code)
        return Response(xml, mimetype='text/xml')
    elif version == "2.01":
        xml = qgenerate.generate_201(country_code)
        return Response(xml, mimetype='text/xml')

    return "ERROR: UNKNOWN VERSION"