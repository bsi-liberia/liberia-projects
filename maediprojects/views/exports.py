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
from maediprojects.lib import util


blueprint = Blueprint('exports', __name__, url_prefix='/', static_folder='../static')

ALLOWED_EXTENSIONS = set(['xlsx', 'xls'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Legacy URL
@blueprint.route("/export/")
def export_redirect():
    return redirect(url_for("exports.export"))

@blueprint.route("/exports/")
def export():
    reporting_orgs = qorganisations.get_reporting_orgs()
    available_fys_fqs = util.available_fy_fqs_as_dict()
    previous_fy_fq = util.column_data_to_string(util.previous_fy_fq())
    currencies = qexchangerates.get_currencies()
    def make_expanded():
        budget_preparation_month = 3
        if datetime.datetime.utcnow().date().month == budget_preparation_month:
            return {"mtef": " in", "disbursements": ""}
        else:
            return {"mtef": "", "disbursements": " in "}
    expanded = make_expanded()
    return render_template("export.html",
                loggedinuser = current_user,
                funding_orgs=reporting_orgs,
                previous_fy_fq = previous_fy_fq,
                available_fys_fqs = available_fys_fqs,
                currencies = currencies,
                expanded = expanded)

@blueprint.route("/exports/import/", methods=["POST", "GET"])
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
        if request.args.get('mtef'):
            result = qgenerate_xlsx.import_xls_mtef(file)
            if result > 0: flash("{} activities successfully updated!".format(result), "success")
            else: flash("""No activities were updated. No updated MTEF projections
            were found. Check that you selected the correct file and that it
            contains update MTEF projections data. It must be formatted according to
            the AMCU template format. You can download a copy of this template
            below.""", "warning")
        elif request.args.get('mtef') == None:
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
        return redirect(url_for('exports.export'))
    flash("Sorry, there was an error, and that file could not be imported", "danger")
    return redirect(url_for('exports.export'))

@blueprint.route("/exports/activities.csv")
def activities_csv():
    data = qgenerate_csv.generate_csv()
    data.seek(0)
    return Response(data, mimetype="text/csv")

@blueprint.route("/exports/activities_external_transactions.xlsx")
def activities_xlsx_transactions():
    data = qgenerate_xlsx.generate_xlsx_transactions(u"domestic_external", u"external")
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_external.xlsx")
def activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx(u"domestic_external", u"external")
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_all.xlsx")
def all_activities_xlsx():
    data = qgenerate_xlsx.generate_xlsx()
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/activities_filtered.xlsx")
def all_activities_xlsx_filtered():
    arguments = request.args.to_dict()
    data = qgenerate_xlsx.generate_xlsx_filtered(arguments)
    data.seek(0)
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@blueprint.route("/exports/export_template.xlsx")
@blueprint.route("/exports/export_template/<organisation_id>.xlsx")
def export_donor_template(organisation_id=None, mtef=False):
    if request.args.get('mtef'):
        fyfq_string = u"MTEF Forward Projections"
        mtef = True
    else:
        fyfq_string = util.column_data_to_string(util.previous_fy_fq())
        mtef = False
    if organisation_id:
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
    data = qgenerate_xlsx.generate_xlsx_export_template(activities, mtef)
    data.seek(0)
    return send_file(data, as_attachment=True, attachment_filename=filename,
        cache_timeout=5)
