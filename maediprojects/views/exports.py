from collections import defaultdict
import datetime

from flask import Blueprint, request, \
    url_for, Response, send_file, redirect, flash, make_response, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, jwt_optional
from maediprojects.query import activity as qactivity
from maediprojects.query import organisations as qorganisations
from maediprojects.query import generate_csv as qgenerate_csv
from maediprojects.query import generate_xlsx as qgenerate_xlsx
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import import_psip_transactions as qimport_psip_transactions
from maediprojects.query import import_client_connection as qimport_client_connection
from maediprojects.query import user as quser
from maediprojects.lib import util


blueprint = Blueprint('exports', __name__, url_prefix='/', static_folder='../static')

ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.route("/api/client-connection/")
@jwt_required
@quser.permissions_required("edit", "external")
def wb_client_connection():
    return qimport_client_connection.import_transactions_from_file()


@blueprint.route("/api/exports/import_psip/", methods=["POST"])
@jwt_required
@quser.permissions_required("edit", "domestic")
def import_psip_transactions(fiscal_year=None):
    if 'file' not in request.files:
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    if 'fiscal_year' in request.form and request.form['fiscal_year'] != '':
        fiscal_year = request.form.get('fiscal_year')
    file = request.files['file']
    if file.filename == '':
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    if file and allowed_file(file.filename):
        result = qimport_psip_transactions.import_transactions_from_upload(file, fiscal_year)
        if result > 0:
            return make_response(jsonify({
                'msg': "{} activities successfully updated!".format(result)
            }), 200)
        else:
            return make_response(jsonify({'msg': """"No activities were updated. Ensure that projects have the correct
        IFMIS project code specified under the "project code" field."""}), 200)
    return make_response(jsonify({'msg': "Sorry, but that file cannot be imported. It must be of type xls or xlsx."}), 400)


@blueprint.route("/api/exports/import/", methods=["POST"])
@jwt_required
@quser.permissions_required("edit", "external")
def import_template():
    if 'file' not in request.files:
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    file = request.files['file']
    if file.filename == '':
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    if file and allowed_file(file.filename):
        if request.form.get('template_type') == 'mtef':
            result_messages, result_rows = qgenerate_xlsx.import_xls_mtef(file)
            if result_rows > 0:
                return make_response(jsonify({
                    'msg': "{} activities successfully updated!".format(result_rows),
                    'messages': result_messages
                }), 200)
            else:
                return make_response(jsonify({'msg': """No activities were updated. No updated MTEF projections
            were found. Check that you selected the correct file and that it
            contains updated MTEF projections data. It must be formatted according to
            the AMCU template format. You can download a copy of this template
            on this page.""",
            'messages': result_messages}), 200)
        elif request.form.get('template_type') == 'disbursements':
            fy_fq = util.previous_fy_fq() #FIXME request.form['fy_fq']
            # For each sheet: convert to dict
            # For each line in each sheet:
            # Process (financial data) import column
            # If no data in that FQ: then import
            # If there was data for that FY: then don't import
            result_messages, result_rows = qgenerate_xlsx.import_xls(file, fy_fq)
            if result_rows > 0:
                return make_response(jsonify({
                    'msg': "{} activities successfully updated!".format(result_rows),
                    'messages': result_messages
                }), 200)
            else:
                return make_response(jsonify({'msg': """No activities were updated. No updated disbursements
            were found. Check that you selected the correct file and that it
            contains updated {} data. It must be formatted according to
            the AMCU template format. You can download a copy of this template
            on this page.""".format(util.column_data_to_string(fy_fq)),
            'messages': result_messages
            }), 200)
    return make_response(jsonify({'msg': "Sorry, but that file cannot be imported. It must be of type xls or xlsx."}), 400)

@blueprint.route("/api/exports/activities.csv")
@jwt_optional
@quser.permissions_required("view")
def activities_csv():
    data = qgenerate_csv.generate_csv()
    data.seek(0)
    return Response(data, mimetype="text/csv")

@blueprint.route("/api/exports/activities_external_transactions.xlsx")
@jwt_optional
@quser.permissions_required("view", "external")
def activities_xlsx_transactions():
    data = qgenerate_xlsx.generate_xlsx_transactions(u"domestic_external", u"external")
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/api/exports/activities_<domestic_external>.xlsx")
@jwt_optional
@quser.permissions_required("view", "external")
def activities_xlsx(domestic_external="external"):
    data = qgenerate_xlsx.generate_xlsx_filtered({"domestic_external": domestic_external})
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/api/exports/activities_all.xlsx")
@jwt_optional
@quser.permissions_required("view")
def all_activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx_filtered()
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/api/exports/activities_filtered.xlsx")
@jwt_optional
@quser.permissions_required("view")
def all_activities_xlsx_filtered():
    arguments = request.args.to_dict()
    data = qgenerate_xlsx.generate_xlsx_filtered(arguments)
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/api/exports/export_template.xlsx")
@blueprint.route("/api/exports/export_template/<organisation_id>.xlsx")
@jwt_optional
@quser.permissions_required("view")
def export_donor_template(organisation_id=None, mtef=False, currency=u"USD", headers=None):
    if request.args.get('template') == 'mtef':
        fyfq_string = u"MTEF Forward Projections"
        mtef = True
    else:
        fyfq_string = util.column_data_to_string(util.previous_fy_fq())
        mtef = False
    currency = request.args.get("currency_code", u"USD")
    organisation_id = request.args.get('reporting_organisation_id', None)
    headers = request.args.get("headers", "")
    headers = headers.split(",")
    if organisation_id and organisation_id != "all":
        reporting_org_name = qorganisations.get_organisation_by_id(
            organisation_id).name
        filename = "AMCU {} Template {}.xlsx".format(fyfq_string, reporting_org_name)
        activities = {reporting_org_name: qactivity.list_activities_by_filters({
            u"reporting_org_id": organisation_id}) }
    else:
        filename = "AMCU {} Template All Donors.xlsx".format(fyfq_string)
        all_activities = qactivity.list_activities_by_filters({
                u"domestic_external": u"external"
            })

        activities = defaultdict(list)
        for a in all_activities:
            activities[a.reporting_org.name].append(a)
    data = qgenerate_xlsx.generate_xlsx_export_template(activities, mtef, currency, headers)
    if not data: return redirect(url_for('exports.export'))
    data.seek(0)
    return send_file(data, as_attachment=True, attachment_filename=filename,
        cache_timeout=5)
