from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
                            
from maediprojects import app, db, models
from maediprojects.query import activity as siactivity

import json

@app.route("/activities/new/", methods=['GET', 'POST'])
def activity_new():
    if request.method == "GET":
        return render_template("activity_edit.html",
                    activity = {},
                    loggedinuser=current_user,
                              )

    elif request.method == "POST":
        # Create new activity
        data = request.form.to_dict()
        a = siactivity.create_activity(data)
        if a:
            flash("Successfully added your activity", "success")
        else:
            flash("An error occurred and your activity couldn't be added", "danger")
        return redirect(url_for('activity_edit', activity_id=a.id))

@app.route("/activities/<activity_id>/edit/")
def activity_edit(activity_id):
    activity = siactivity.get_activity(activity_id)
    return render_template("activity_edit.html",
                activity = activity,
                loggedinuser=current_user,
                          )

@app.route("/activities/<activity_id>/edit/update_result/", methods=['POST'])
def activity_edit_result_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = siactivity.update_result_attr(data)
    if update_status == True:
        return "success"
    return "error"

@app.route("/activities/<activity_id>/edit/update_indicator/", methods=['POST'])
def activity_edit_indicator_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = siactivity.update_indicator_attr(data)
    if update_status == True:
        return "success"
    return "error"

@app.route("/activities/<activity_id>/edit/update_period/", methods=['POST'])
def activity_edit_period_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': request.form['id']
    }
    update_status = siactivity.update_indicator_period_attr(data)
    if update_status == True:
        return "success"
    return "error"

@app.route("/activities/<activity_id>/edit/delete_result_data/", methods=['POST'])
def activity_delete_result_data(activity_id):
    data = {
        'id': request.form['id'],
        'result_type': request.form['result_type']
    }
    delete_status = siactivity.delete_result_data(data)
    if delete_status == True:
        return "success"
    return "error"

@app.route("/activities/<activity_id>/edit/add_result_data/", methods=['POST'])
def activity_add_results_data(activity_id):
    data = request.form
    add_status = siactivity.add_result_data(activity_id, data)
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
def activity_edit_attr(activity_id):
    data = {
        'attr': request.form['attr'],
        'value': request.form['value'],
        'id': activity_id,
    }
    update_status = siactivity.update_attr(data)
    if update_status == True:
        return "success"
    return "error"