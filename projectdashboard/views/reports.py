from projectdashboard.views.api import jsonify
from projectdashboard.query import activity as qactivity
from projectdashboard.query import user as quser
from projectdashboard.query import reports as qreports
from projectdashboard.query import counterpart_funding as qcounterpart_funding

from flask import Blueprint, request, \
    url_for, Response, current_app, abort

from flask_jwt_extended import (
    jwt_required
)
from projectdashboard.lib import util
from projectdashboard import models
import datetime
from collections import OrderedDict


blueprint = Blueprint('reports', __name__, url_prefix='/api/reports')


@blueprint.route("/disbursements/psip/")
@jwt_required()
@quser.permissions_required("view", "domestic")
def psip_disbursements_api():
    _current_fy = util.FY("previous")
    current_fy = _current_fy.fiscal_year.name
    fiscal_year = request.args.get("fiscal_year", current_fy)
    start_of_fy = _current_fy.fiscal_year.start
    days_since_fy_began = (
        (datetime.datetime.utcnow().date()-start_of_fy).days)
    progress_time = min(round(days_since_fy_began/365.0*100.0, 2), 100.0)
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'domestic'})
    if start_date is not None:
        fys = [str(fy) for fy in util.fys_in_date_range(start_date, end_date)]
    else:
        fys = []
    return jsonify(activities=qreports.make_appropriations_disbursements_data(fiscal_year),
                   progress_time=progress_time,
                   days_since_fy_began=days_since_fy_began,
                   fy_start_day=datetime.datetime.strftime(
                       start_of_fy, "%d.%m.%Y"),
                   fiscalYears=fys,
                   fiscalYear=str(fiscal_year))


@blueprint.route("/disbursements/aid/")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def aid_disbursements_api():
    _current_fy = util.FY("previous")
    current_fy = _current_fy.fiscal_year.name
    fiscal_year = request.args.get("fiscal_year", current_fy)
    start_of_fy = _current_fy.fiscal_year.start
    days_since_fy_began = (
        (datetime.datetime.utcnow().date()-start_of_fy).days)
    progress_time = min(round(days_since_fy_began/365.0*100.0, 2), 100.0)
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'external'})
    start_date = max(start_date, current_app.config['EARLIEST_DATE'])
    fys = [str(fy) for fy in util.fys_in_date_range(start_date, end_date)]

    return jsonify(activities=qreports.make_forwardspends_disbursements_data(fiscal_year),
                   progress_time=progress_time,
                   days_since_fy_began=days_since_fy_began,
                   fy_start_day=datetime.datetime.strftime(
                       start_of_fy, "%d.%m.%Y"),
                   fiscalYears=fys,
                   fiscalYear=str(fiscal_year))


@blueprint.route("/project-development-tracking/")
@jwt_required()
@quser.permissions_required("view", "domestic")
def project_development_tracking():
    current_fy = util.FY("previous").fiscal_year.name
    fiscal_year = request.args.get("fiscal_year", current_fy)
    activities = models.Activity.query.filter_by(
        domestic_external=u"domestic"
    ).all()
    milestones = models.Milestone.query.filter_by(
        domestic_external=u"domestic"
    ).order_by(
        models.Milestone.milestone_order
    ).all()

    sum_appropriations = qreports.sum_transactions(
        fiscal_year, 0, 'domestic', 'sum_appropriations', 'C')
    sum_allotments = qreports.sum_transactions(
        fiscal_year, 0, 'domestic', 'sum_allotments', '99-A')
    sum_disbursements = qreports.sum_transactions(
        fiscal_year, 0, 'domestic', 'sum_disbursements', 'D')

    def annotate_activity(activity):
        out = {}
        out = OrderedDict({
            'id': activity.id,
            'title': activity.title,
            'implementer': ", ".join([implementer.name for implementer in activity.implementing_organisations]),
            'sum_appropriations': sum_appropriations.get(activity.id, 0.00),
            'sum_allotments': sum_allotments.get(activity.id, 0.00),
            'sum_disbursements': sum_disbursements.get(activity.id, 0.00)
        })
        [out.update({ms['name']: ms['achieved']})
         for ms in activity.milestones_data]
        return out

    milestone_data = [annotate_activity(activity) for activity in activities]

    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'domestic'})
    if start_date is not None:
        fys = list(
            map(lambda f: str(f), util.fys_in_date_range(start_date, end_date)))
    else:
        fys = []

    return jsonify(activities=milestone_data,
                   milestones=[milestone.name for milestone in milestones],
                   fiscalYears=fys,
                   fiscalYear=str(fiscal_year))


@blueprint.route("/counterpart-funding/")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def counterpart_funding():
    next_fy = util.FY("current").fiscal_year.name
    fiscal_year = request.args.get("fiscal_year", next_fy)
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'external'})
    next_fy_end_date = util.FY("next").date("end")
    fys = [str(fy) for fy in util.fys_in_date_range(
        start_date, max(end_date, next_fy_end_date))]

    def annotate_activity(activity):
        return {
            'id': activity.id,
            'title': activity.title,
            'reporting_org_name': activity.reporting_org.name,
            'sector_name': ", ".join([sector.codelist_code.name for sector in activity.classification_data.get('mtef-sector', {}).get('entries', [])]),
            'ministry_name': ", ".join([ministry.codelist_code.name for ministry in activity.classification_data.get('aligned-ministry-agency', {}).get('entries', [])]),
            'gol_requested': activity._fy_counterpart_funding,
            'donor_planned': activity._fy_forwardspends
        }

    activities = [annotate_activity(activity) for activity in
        qcounterpart_funding.annotate_activities_with_aggregates(fiscal_year)]

    return jsonify(
        fy=util.FY("next").fy_fy(),
        activities=activities,
        fiscalYears=fys,
        fiscalYear=str(fiscal_year)
    )


@blueprint.route("/results/")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def results():
    def annotate_activity(activity):
        return {
            'id': activity.id,
            'title': activity.title,
            'reporting_org_name': activity.reporting_org.name,
            'implementer_name': ", ".join([org.name for org in activity.implementing_organisations]),
            'results_average': round(activity.results_average) if activity.results_average is not None else None,
            'results_average_status': activity.results_average_status
        }

    activities = [annotate_activity(activity) for activity in
                          models.Activity.query.filter(
        models.Activity.results.any(),
        models.Activity.domestic_external == 'external'
    ).all()
    ]

    return jsonify(
        activities=activities
    )
