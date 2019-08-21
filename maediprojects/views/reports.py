import datetime
import functools

from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user

from maediprojects import models
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.query import reports as qreports
from maediprojects.lib import util


blueprint = Blueprint('reports', __name__, url_prefix='/', static_folder='../static')


@blueprint.route("/reports/dataquality/")
@login_required
def dataquality_redir():
    return redirect(url_for('management.management'))


@blueprint.route("/reports/milestones/")
@login_required
def milestones():
    activities = models.Activity.query.filter_by(
            domestic_external=u"domestic"
        ).all()
    milestones = models.Milestone.query.filter_by(
            domestic_external=u"domestic"
        ).order_by(
            models.Milestone.milestone_order
        ).all()

    return render_template(
        "reports/milestones.html",
        activities=activities,
        milestones=milestones,
        loggedinuser=current_user
    )


@blueprint.route("/reports/counterpart-funding/")
@login_required
def counterpart_funding():
    activities = models.Activity.query.filter_by(
            domestic_external=u"external"
        ).all()

    activities = qcounterpart_funding.annotate_activities_with_aggregates(
        activities)

    return render_template(
        "reports/counterpart_funding.html",
        activities = activities,
        loggedinuser = current_user
    )


@blueprint.route("/reports/results/")
@login_required
def results():
    activities = models.Activity.query.filter_by(
            domestic_external=u"external",
        ).filter(
            models.Activity.results.any()
        ).all()

    return render_template(
        "reports/results.html",
        activities = activities,
        loggedinuser = current_user
    )


@blueprint.route("/api/disbursements/aid/")
@login_required
def aid_disbursements_api():
    fiscal_year = int(request.args.get("fiscal_year", 2018))
    start_of_fy = util.fq_fy_to_date(1, fiscal_year, start_end='start')
    days_since_fy_began = ((datetime.datetime.utcnow()-start_of_fy).days)
    progress_time = min(round(days_since_fy_began/365.0*100.0, 2), 100.0)

    return jsonify(activities=qreports.make_forwardspends_disbursements_data(fiscal_year),
        progress_time=progress_time,
        days_since_fy_began=days_since_fy_began,
        fy_start_day=datetime.datetime.strftime(start_of_fy, "%d.%m.%Y"))


@blueprint.route("/reports/disbursements/aid/")
@login_required
def aid_disbursements():
    return render_template(
        "reports/aid_disbursements.html",
        loggedinuser=current_user
    )

@blueprint.route("/reports/disbursements/psip/")
@login_required
def psip_disbursements():
    def filter_relevant(finances, transaction_type=u'D'):
        year_end = datetime.date(2019,06,30)
        year_start = datetime.date(2018,07,01)
        if hasattr(finances, 'transaction_date'):
            return bool((finances.transaction_date <= year_end) and
                (finances.transaction_date >= year_start) and
                (finances.transaction_type==transaction_type))
        elif hasattr(finances, 'period_end_date'):
            return bool((finances.period_end_date <= year_end) and
                (finances.period_end_date >= year_start))

    def make_pct(value1, value2):
        try:
            return round((float(value1)/float(value2))*100.0, 2)
        except Exception:
            return 0.0

    # Show actual disbursement as % of total
    # Show time as % of total
    # Show in-year disbursement as % of mtef projections
    activities = models.Activity.query.filter_by(
        domestic_external=u"domestic").all()

    out = []


    options = {
        u"commitments": u"Appropriation",
        u"disbursements": u"Actual Disbursement",
        u"allotments": u"Allotment",
       #u"forwardspends": u"Planned Disbursements"
    }
    denominator = "commitments"
    numerator = "disbursements"
    cutoff = "commitments" #denominator
    cutoff_amount = 0 # in millions

    for activity in activities:
        aggs = {
            "disbursements": sum(map(lambda l: l.transaction_value, filter(functools.partial(filter_relevant, transaction_type=u"D"), activity.disbursements))),
            "commitments": sum(map(lambda l: l.transaction_value, filter(functools.partial(filter_relevant, transaction_type=u"C"), activity.commitments))),
            "allotments": sum(map(lambda l: l.transaction_value, filter(functools.partial(filter_relevant, transaction_type=u"99-A"), activity.allotments)))
            #"forwardspends": sum_forwardspends = sum(map(lambda l: l.value, filter(functools.partial(filter_relevant, transaction_type=u"D"), activity.forwardspends)))
        }
        sum_numerator = aggs[numerator]
        sum_denominator = aggs[denominator]
        pct = make_pct(sum_numerator,sum_denominator)
        if (aggs[cutoff]>(cutoff_amount*1000000)):
            act = activity.as_jsonable_dict()
            act['sum_numerator'] = "{:,.2f}".format(sum_numerator),
            act['sum_denominator'] = "{:,.2f}".format(sum_denominator),
            act['pct_difference'] = pct
            out.append(act)
    current_year, current_quarter = util.date_to_fy_fq(datetime.datetime.utcnow())
    start_of_fy = util.fq_fy_to_date(1, current_year, start_end='start')
    days_since_fy_begin = ((datetime.datetime.utcnow()-start_of_fy).days)
    progress_time = round(days_since_fy_begin/365.0*100.0, 2)


    return render_template("reports/psip_disbursements.html",
                activities = out,
                progress_time = progress_time,
                days_since_fy_begin = days_since_fy_begin,
                fy_start_day = datetime.datetime.strftime(start_of_fy, "%d.%m.%Y"),
                loggedinuser = current_user,
                numerator = options[numerator],
                denominator = options[denominator],
                cutoff = options[cutoff],
                cutoff_amount = cutoff_amount
        )
