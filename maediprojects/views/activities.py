import datetime

from flask import Blueprint, flash, request, \
    redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required

from maediprojects.query import codelists as qcodelists
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import organisations as qorganisations
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import user as quser
from maediprojects.lib import codelists


blueprint = Blueprint('activities', __name__, url_prefix='/', static_folder='../static')


@blueprint.route("/api/activities/<activity_id>/delete/", methods=['POST'])
@jwt_required
@quser.permissions_required("edit")
def activity_delete(activity_id):
    result = qactivity.delete_activity(activity_id)
    if result:
        return jsonify({'msg': "Successfully deleted that activity"}, 200)
    else:
        return jsonify({'msg': "Sorry, unable to delete that activity"}, 500)


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


@blueprint.route("/api/activities/<activity_id>/edit/update_activity/", methods=['POST'])
@jwt_required
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