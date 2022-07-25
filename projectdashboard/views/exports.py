from collections import defaultdict
import io
import sys
import re
import zipfile

from flask import Blueprint, request, abort, \
    Response, send_file, make_response, jsonify
from flask_jwt_extended import jwt_required
from projectdashboard.query import activity as qactivity
from projectdashboard.query import organisations as qorganisations
from projectdashboard.query import generate_csv as qgenerate_csv
from projectdashboard.query import generate_xlsx as qgenerate_xlsx
from projectdashboard.query import import_psip_transactions as qimport_psip_transactions
from projectdashboard.query import import_client_connection as qimport_client_connection
from projectdashboard.query import user as quser
from projectdashboard.query import generate_docx as qgenerate_docx
from projectdashboard.lib import util
from projectdashboard import models


blueprint = Blueprint('exports', __name__, url_prefix='/',
                      static_folder='../static')

ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.route("/api/project-brief/<activity_id>.docx")
@jwt_required()
def export_project_brief(activity_id):
    brief = qgenerate_docx.make_doc(activity_id)
    brief.seek(0)
    return Response(brief,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@blueprint.route("/api/sector-brief/<sector_id>.docx")
@jwt_required()
def export_sector_brief(sector_id):
    brief = qgenerate_docx.make_sector_doc(sector_id)
    brief.seek(0)
    return Response(brief,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@blueprint.route("/api/project-brief/donor/<reporting_org_id>.zip")
@jwt_required()
def export_project_brief_donor(reporting_org_id):
    zip_buffer = io.BytesIO()
    activities = qactivity.get_activities_by_reporting_org_id(reporting_org_id)

    def make_title(title):
        if sys.version_info.major == 2:
            return re.sub("/", "-", title.encode("utf-8"))
        return re.sub("/", "-", title)

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for activity in activities:
            brief = qgenerate_docx.make_doc(activity.id)
            brief.seek(0)
            zip_file.writestr("{} - {}.docx".format(activity.id,
                              make_title(activity.title)), brief.getvalue())
    zip_buffer.seek(0)
    return Response(zip_buffer,
        mimetype="application/zip, application/octet-stream, application/x-zip-compressed, multipart/x-zip")


@blueprint.route("/api/client-connection/", methods=["POST"])
@jwt_required()
@quser.permissions_required("edit", "external")
def wb_client_connection():
    for file in request.files.getlist("file"):
        qimport_client_connection.load_transactions_from_file(file)
    return 'ok'


@blueprint.route("/api/client-connection/transactions/")
@jwt_required()
@quser.permissions_required("edit", "external")
def wb_client_connection_transactions():
    transactions_db = models.ClientConnectionData.query.filter_by(processed=False
        ).all()
    return jsonify(transactions = [transaction.as_dict() for transaction in transactions_db])


@blueprint.route("/api/client-connection/similar/")
@jwt_required()
def wb_client_connection_similar_activities():
    cc_projects = [{
        'project_code': cc_project.project_code,
        'project_title': cc_project.project_title
        } for cc_project in qimport_client_connection.client_connection_projects()]
    db_activities = [{
        'id': activity.id,
        'iati_identifier': activity.iati_identifier,
        'title': activity.title
        } for activity in qactivity.list_activities_by_filters({'reporting_org_id': 11})]
    return jsonify(
        matches=qimport_client_connection.closest_matches_groupings(),
        clientConnectionProjects = cc_projects,
        dbActivities = db_activities
    )


@blueprint.route("/api/client-connection/import/", methods=['POST'])
@jwt_required()
def wb_client_connection_import_data():
    data = request.get_json()
    qimport_client_connection.import_data(cc_project_code=data['ccProjectCode'],
        activity_ids=data['selectedActivities'],
        activities_fields_options=data['selectedActivitiesFieldsOptions'])
    return "true"


@blueprint.route("/api/client-connection/import-all/", methods=['GET'])
@jwt_required()
def wb_client_connection_import_all_data():
    status = qimport_client_connection.import_all_data()
    return jsonify(status=status)


@blueprint.route("/api/exports/import_psip/", methods=["POST"])
@jwt_required()
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
        result = qimport_psip_transactions.import_transactions_from_upload(
            file, fiscal_year)
        if result > 0:
            return make_response(jsonify({
                'msg': "{} activities successfully updated!".format(result)
            }), 200)
        else:
            return make_response(jsonify({'msg': """"No activities were updated.
        Ensure that projects have the correct
        IFMIS project code specified under the "project code" field."""}), 200)
    return make_response(jsonify({'msg': """Sorry, but that file cannot be imported.
        It must be of type xls or xlsx."""}), 400)


@blueprint.route("/api/exports/import/", methods=["POST"])
@jwt_required()
@quser.permissions_required("edit", "external")
def import_template():
    if 'file' not in request.files:
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    file = request.files['file']
    if file.filename == '':
        return make_response(jsonify({'msg': 'Please select a file.'}), 400)
    if file and allowed_file(file.filename):
        headers = request.form.get('import_headers').split(",")
        if headers == ['']: headers = []
        activity_headers = request.form.get('activity_headers', '').split(",")
        if activity_headers == ['']: activity_headers = []
        try:
            if request.form.get('template_type') == 'mtef':
                result_messages, result_rows = qgenerate_xlsx.import_xls_mtef(file, headers, activity_headers)
                if result_rows > 0:
                    return make_response(jsonify({
                        'msg': "{} activities successfully updated!".format(result_rows),
                        'messages': result_messages
                    }), 200)
                else:
                    return make_response(jsonify({'msg': """No activities were updated.
                No updated MTEF projections
                were found. Check that you selected the correct file and that it
                contains updated MTEF projections data. It must be formatted according to
                the AMCU template format. You can download a copy of this template
                on this page.""",
                  'messages': result_messages}), 200)
            elif request.form.get('template_type') == 'disbursements':
                # For each sheet: convert to dict
                # For each line in each sheet:
                # Process (financial data) import column
                # If no data in that FQ: then import
                # If there was data for that FY: then don't import
                result_messages, result_rows = qgenerate_xlsx.import_xls(
                    file, headers, activity_headers)
                if result_rows > 0:
                    return make_response(jsonify({
                        'msg': "{} activities successfully updated!".format(result_rows),
                        'messages': result_messages
                    }), 200)
                else:
                    return make_response(jsonify({'msg': """No activities were updated.
                        No updated disbursements
                were found. Check that you selected the correct file and that it
                contains updated {} data. It must be formatted according to
                the AMCU template format. You can download a copy of this template
                on this page.""".format(", ".join(headers)),
                        'messages': result_messages
                    }), 200)
        except Exception as e:
            return make_response(jsonify({'msg': str(e)}), 400)
    return make_response(jsonify({'msg': """Sorry, but that file cannot be imported.
        It must be of type xls or xlsx."""}), 400)


@blueprint.route("/api/exports/activities.csv")
@jwt_required(optional=True)
@quser.permissions_required("view")
def activities_csv():
    data = qgenerate_csv.generate_csv()
    data.seek(0)
    return Response(data, mimetype="text/csv")


@blueprint.route("/api/exports/activities_external_transactions.xlsx")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def activities_xlsx_transactions():
    data = qgenerate_xlsx.generate_xlsx_transactions(
        "domestic_external", "external")
    data.seek(0)
    return Response(data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@blueprint.route("/api/exports/activities_<domestic_external>.xlsx")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def activities_xlsx(domestic_external="external"):
    data = qgenerate_xlsx.generate_xlsx_filtered(
        {"domestic_external": domestic_external})
    data.seek(0)
    return Response(data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@blueprint.route("/api/exports/activities_all.xlsx")
@jwt_required(optional=True)
@quser.permissions_required("view")
def all_activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx_filtered()
    data.seek(0)
    return Response(data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@blueprint.route("/api/exports/activities_filtered.xlsx")
@jwt_required(optional=True)
@quser.permissions_required("view")
def all_activities_xlsx_filtered():
    arguments = request.args.to_dict()
    data = qgenerate_xlsx.generate_xlsx_filtered(arguments)
    data.seek(0)
    return Response(data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@blueprint.route("/api/exports/export_template.xlsx")
@blueprint.route("/api/exports/export_template/<organisation_id>.xlsx")
@jwt_required(optional=True)
@quser.permissions_required("view")
def export_donor_template(organisation_id=None, mtef=False, currency="USD", headers=None):
    if request.args.get('template') == 'mtef':
        fyfq_string = "MTEF Forward Projections"
        mtef = True
    else:
        fyfq_string = util.column_data_to_string(util.previous_fy_fq())
        mtef = False
    currency = request.args.get("currency_code", "USD")
    organisation_id = request.args.get('reporting_organisation_id', None)
    headers = request.args.get("headers", "")
    headers = headers.split(",")
    if organisation_id and organisation_id != "all":
        reporting_org_name = qorganisations.get_organisation_by_id(
            organisation_id).name
        filename = "AMCU {} Template {}.xlsx".format(
            fyfq_string, reporting_org_name)
        activities = {reporting_org_name: qactivity.list_activities_by_filters({
            "reporting_org_id": organisation_id})}
    else:
        filename = "AMCU {} Template All Donors.xlsx".format(fyfq_string)
        all_activities = qactivity.list_activities_by_filters({
            "domestic_external": "external"
        })

        activities = defaultdict(list)
        for a in all_activities:
            activities[a.reporting_org.name].append(a)
    data = qgenerate_xlsx.generate_xlsx_export_template(
        activities, mtef, currency, headers)
    if not data:
        return abort(404)
    data.seek(0)
    return send_file(data, as_attachment=True, attachment_filename=filename,
                     cache_timeout=5)
