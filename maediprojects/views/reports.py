from maediprojects.views.api import jsonify
from maediprojects.query import activity as qactivity
from maediprojects.query import user as quser
from maediprojects.query import reports as qreports
from maediprojects.query import counterpart_funding as qcounterpart_funding

from flask import Blueprint, request, \
    url_for, Response, current_app, abort

from flask_jwt_extended import (
    jwt_required
)
from maediprojects.lib import util
from maediprojects import models
import datetime


blueprint = Blueprint('reports', __name__, url_prefix='/api/reports')


@blueprint.route("/disbursements/psip/")
@jwt_required()
@quser.permissions_required("view", "domestic")
def psip_disbursements_api():
    current_fy, _ = util.FY("previous").numeric()
    fiscal_year = int(request.args.get("fiscal_year", current_fy))
    start_of_fy = util.fq_fy_to_date(1, fiscal_year, start_end='start')
    days_since_fy_began = ((datetime.datetime.utcnow()-start_of_fy).days)
    progress_time = min(round(days_since_fy_began/365.0*100.0, 2), 100.0)
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'domestic'})
    if start_date is not None:
        fys = list(map(lambda f: str(f), util.fys_in_date_range(start_date, end_date)))
    else:
        fys = []
    return jsonify(activities=qreports.make_appropriations_disbursements_data(fiscal_year),
        progress_time=progress_time,
        days_since_fy_began=days_since_fy_began,
        fy_start_day=datetime.datetime.strftime(start_of_fy, "%d.%m.%Y"),
        fiscalYears=fys,
        fiscalYear = str(fiscal_year))


@blueprint.route("/disbursements/aid/")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def aid_disbursements_api():
    current_fy, _ = util.FY("previous").numeric()
    fiscal_year = int(request.args.get("fiscal_year", current_fy))
    start_of_fy = util.fq_fy_to_date(1, fiscal_year, start_end='start')
    days_since_fy_began = ((datetime.datetime.utcnow()-start_of_fy).days)
    progress_time = min(round(days_since_fy_began/365.0*100.0, 2), 100.0)
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'external'})
    start_date = max(start_date, current_app.config['EARLIEST_DATE'])
    fys = list(map(lambda f: str(f), util.fys_in_date_range(start_date, end_date)))

    return jsonify(activities=qreports.make_forwardspends_disbursements_data(fiscal_year),
        progress_time=progress_time,
        days_since_fy_began=days_since_fy_began,
        fy_start_day=datetime.datetime.strftime(start_of_fy, "%d.%m.%Y"),
        fiscalYears=fys,
        fiscalYear = str(fiscal_year))

@blueprint.route("/project-development-tracking/")
@jwt_required()
@quser.permissions_required("view", "domestic")
def project_development_tracking():
    current_fy, _ = util.FY("previous").numeric()
    fiscal_year = int(request.args.get("fiscal_year", current_fy))
    activities = models.Activity.query.filter_by(
            domestic_external=u"domestic"
        ).all()
    milestones = models.Milestone.query.filter_by(
            domestic_external=u"domestic"
        ).order_by(
            models.Milestone.milestone_order
        ).all()

    sum_appropriations = qreports.sum_transactions(fiscal_year, 0, 'domestic', 'sum_appropriations', 'C')
    sum_allotments = qreports.sum_transactions(fiscal_year, 0, 'domestic', 'sum_allotments', '99-A')
    sum_disbursements = qreports.sum_transactions(fiscal_year, 0, 'domestic', 'sum_disbursements', 'D')

    def annotate_activity(activity):
        out = {}
        out = OrderedDict({
            'id': activity.id,
            'title': activity.title,
            'implementer': ", ".join(list(map(lambda io: io.name, activity.implementing_organisations))),
            'sum_appropriations': sum_appropriations.get(activity.id, 0.00),
            'sum_allotments': sum_allotments.get(activity.id, 0.00),
            'sum_disbursements': sum_disbursements.get(activity.id, 0.00)
        })
        [out.update({ms['name']: ms['achieved']}) for ms in activity.milestones_data]
        return out

    milestone_data = list(map(lambda a: annotate_activity(a), activities))

    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'domestic'})
    if start_date is not None:
        fys = list(map(lambda f: str(f), util.fys_in_date_range(start_date, end_date)))
    else:
        fys = []

    return jsonify(activities=milestone_data,
        milestones = list(map(lambda m: m.name, milestones)),
        fiscalYears = fys,
        fiscalYear = str(fiscal_year))


@blueprint.route("/counterpart-funding/")
@jwt_required(optional=True)
@quser.permissions_required("view", "external")
def counterpart_funding():
    if datetime.datetime.utcnow().month > 6:
        next_fy, _ = util.FY("previous").numeric()
    else:
        next_fy, _ = util.FY("next").numeric()
    fiscal_year = int(request.args.get("fiscal_year", next_fy))
    start_date, end_date = qactivity.get_earliest_latest_dates_filter(
        {'key': 'domestic_external', 'val': 'external'})
    fys = list(map(lambda f: str(f), util.fys_in_date_range(start_date, end_date)))

    def annotate_activity(activity):
        return {
            'id': activity.id,
            'title': activity.title,
            'reporting_org_name': activity.reporting_org.name,
            'ministry_name': ", ".join(list(map(lambda ministry: ministry.codelist_code.name, activity.classification_data.get('aligned-ministry-agency', {}).get('entries', [])))),
            'gol_requested': activity._fy_counterpart_funding,
            'donor_planned': activity._fy_forwardspends
        }

    activities = list(map(lambda activity: annotate_activity(activity),
        qcounterpart_funding.annotate_activities_with_aggregates(fiscal_year)))

    return jsonify(
        fy=util.FY("next").fy_fy(),
        activities = activities,
        fiscalYears = fys,
        fiscalYear = str(fiscal_year)
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
            'implementer_name': ", ".join(list(map(lambda org: org.name, activity.implementing_organisations))),
            'results_average': activity.results_average,
            'results_average_status': activity.results_average_status
        }

    activities = list(map(lambda activity: annotate_activity(activity),
        models.Activity.query.filter(
            models.Activity.results.any(),
            models.Activity.domestic_external=='external'
        ).all()
    ))

    return jsonify(
        activities = activities
    )
