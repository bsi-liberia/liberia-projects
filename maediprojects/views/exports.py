from collections import defaultdict
import datetime

from flask import Blueprint, request, \
    url_for, Response, send_file, render_template, redirect, flash
from flask_login import login_required, current_user

from maediprojects.query import activity as qactivity
from maediprojects.query import organisations as qorganisations
from maediprojects.query import generate_csv as qgenerate_csv
from maediprojects.query import generate_xlsx as qgenerate_xlsx
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import import_psip_transactions as qimport_psip_transactions
from maediprojects.query import user as quser
from maediprojects.lib import util


blueprint = Blueprint('exports', __name__, url_prefix='/', static_folder='../static')

ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Legacy URL
@blueprint.route("/export/")
@login_required
@quser.permissions_required("view")
def export_redirect():
    return redirect(url_for("exports.export"))


@blueprint.route("/exports/")
@login_required
@quser.permissions_required("view")
def export():
    reporting_orgs = qorganisations.get_reporting_orgs()
    available_fys_fqs = util.available_fy_fqs_as_dict()
    previous_fy_fq = util.column_data_to_string(util.previous_fy_fq())
    currencies = qexchangerates.get_currencies()
    return render_template("export.html",
                loggedinuser = current_user)

@blueprint.route("/exports/import_psip/", methods=["POST", "GET"])
@login_required
@quser.permissions_required("edit")
def import_psip_transactions(fiscal_year=None):
    if request.method == "GET": return(redirect(url_for('exports.export')))
    if 'file' not in request.files:
        flash('Please select a file.', "warning")
        return redirect(request.url)
    if 'fiscal_year' in request.form and request.form['fiscal_year'] != '':
        fiscal_year = request.form.get('fiscal_year')
    file = request.files['file']
    if file.filename == '':
        flash('Please select a file.', "warning")
        return redirect(request.url)
    if file and allowed_file(file.filename):
        result = qimport_psip_transactions.import_transactions_from_upload(file, fiscal_year)
        if result > 0: flash("{} activities successfully updated!".format(result), "success")
        else: flash("""No activities were updated. Ensure that projects have the correct
        IFMIS project code specified under the "project code" field.""", "warning")
        return redirect(url_for('exports.export'))
    flash("Sorry, there was an error, and that file could not be imported", "danger")
    return redirect(url_for('exports.export'))


@blueprint.route("/exports/import/", methods=["POST", "GET"])
@login_required
@quser.permissions_required("edit")
def import_template():
    if request.method == "GET": return(redirect(url_for('exports.export')))
    if 'file' not in request.files:
        flash('Please select a file.', "warning")
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Please select a file.', "warning")
        return redirect(request.url)
    if file and allowed_file(file.filename):
        if request.form.get('template_type') == 'mtef':
            result = qgenerate_xlsx.import_xls_mtef(file)
            if result > 0: flash("{} activities successfully updated!".format(result), "success")
            else: flash("""No activities were updated. No updated MTEF projections
            were found. Check that you selected the correct file and that it
            contains update MTEF projections data. It must be formatted according to
            the AMCU template format. You can download a copy of this template
            below.""", "warning")
        elif request.form.get('template_type') == 'disbursements':
            fy_fq = util.previous_fy_fq() #FIXME request.form['fy_fq']
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
        return redirect(url_for('exports.export'))
    flash("Sorry, there was an error, and that file could not be imported", "danger")
    return redirect(url_for('exports.export'))

@blueprint.route("/exports/activities.csv")
@login_required
@quser.permissions_required("view")
def activities_csv():
    data = qgenerate_csv.generate_csv()
    data.seek(0)
    return Response(data, mimetype="text/csv")

@blueprint.route("/exports/activities_external_transactions.xlsx")
@login_required
@quser.permissions_required("view")
def activities_xlsx_transactions():
    data = qgenerate_xlsx.generate_xlsx_transactions(u"domestic_external", u"external")
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_<domestic_external>.xlsx")
@login_required
@quser.permissions_required("view")
def activities_xlsx(domestic_external="external"):
    data = qgenerate_xlsx.generate_xlsx_filtered({"domestic_external": domestic_external})
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_all.xlsx")
@login_required
@quser.permissions_required("view")
def all_activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx_filtered()
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_filtered.xlsx")
@login_required
def all_activities_xlsx_filtered():
    arguments = request.args.to_dict()
    data = qgenerate_xlsx.generate_xlsx_filtered(arguments)
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/export_template.xlsx")
@blueprint.route("/exports/export_template/<organisation_id>.xlsx")
@login_required
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
