from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
                            
from maediprojects import app, db, models
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.lib import codelists

import json

@app.route("/")
def dashboard():
    return render_template("home.html",
                loggedinuser=current_user,
                stats = qactivity.get_stats(current_user),
                activities = qactivity.list_activities_user(current_user)
                          )

@app.route("/activities/new/", methods=['GET', 'POST'])
@login_required
def activity_new():
    if request.method == "GET":
        return render_template("activity_edit.html",
                    # Specify some defaults
                    activity = {
                        "flow_type": "10",
                        "aid_type": "C01",
                        "collaboration_type": "1",
                        "finance_type": "110",
                        "tied_status": "5",
                        "recipient_country_code": current_user.recipient_country_code,
                    },
                    loggedinuser=current_user,
                    codelists = codelists.get_codelists()
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
        return redirect(url_for('activity_edit', activity_id=a.id))

@app.route("/activities/<activity_id>/delete/")
@login_required
def activity_delete(activity_id):
    result = qactivity.delete_activity(activity_id)
    if result:
        flash("Successfully deleted that activity", "success")
    else:
        flash("Sorry, unable to delete that activity", "danger")
    return redirect(url_for("dashboard"))

@app.route("/activities/<activity_id>/edit/")
@login_required
def activity_edit(activity_id):
    activity = qactivity.get_activity(activity_id)
    locations = qlocation.get_locations_country(
                                    activity.recipient_country_code)
    return render_template("activity_edit.html",
                activity = activity,
                loggedinuser=current_user,
                codelists = codelists.get_codelists(),
                locations = locations,
                api_locations_url ="/api/locations/%s/" % activity.recipient_country_code,
                api_activity_locations_url = "/api/activity_locations/%s/" % activity_id,
                api_activity_finances_url = "/api/activity_finances/%s/" % activity_id,
                api_update_activity_finances_url = "/api/activity_finances/%s/update_finances/" % activity_id
          )

@app.route("/activities/<activity_id>/edit/update_result/", methods=['POST'])
@login_required
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

@app.route("/activities/<activity_id>/edit/update_indicator/", methods=['POST'])
@login_required
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

@app.route("/activities/<activity_id>/edit/update_period/", methods=['POST'])
@login_required
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

@app.route("/activities/<activity_id>/edit/delete_result_data/", methods=['POST'])
@login_required
def activity_delete_result_data(activity_id):
    data = {
        'id': request.form['id'],
        'result_type': request.form['result_type']
    }
    delete_status = qactivity.delete_result_data(data)
    if delete_status == True:
        return "success"
    return "error"

@app.route("/activities/<activity_id>/edit/add_result_data/", methods=['POST'])
@login_required
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

@app.route("/activities/<activity_id>/edit/update_activity/", methods=['POST'])
@login_required
def activity_edit_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': activity_id,
    }
    update_status = qactivity.update_attr(data)
    if update_status == True:
        return "success"
    return "error"