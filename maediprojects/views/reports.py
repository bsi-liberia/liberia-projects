import datetime
import functools

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from maediprojects import models
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.lib import util


blueprint = Blueprint('reports', __name__, url_prefix='/', static_folder='../static')


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


@blueprint.route("/reports/disbursements/aid/")
@login_required
def aid_disbursements():
    def filter_relevant(finances, transaction_type=u'D'):
        year_end = datetime.date(2019, 6, 30)
        year_start = datetime.date(2018, 7, 1)
        if hasattr(finances, 'transaction_date'):
            return bool(
                (finances.transaction_date <= year_end) and
                (finances.transaction_date >= year_start) and
                (finances.transaction_type == transaction_type))
        elif hasattr(finances, 'period_end_date'):
            return bool(
                (finances.period_end_date <= year_end) and
                (finances.period_end_date >= year_start))

    def make_pct(value1, value2):
        try:
            return round((float(value1)/float(value2))*100.0, 2)
        except Exception:
            return False

    # Show actual disbursement as % of total
    # Show time as % of total
    # Show in-year disbursement as % of mtef projections
    activities = models.Activity.query.filter_by(
        domestic_external=u"external").all()

    out = []

    for activity in activities:
        sum_disbursements = sum(map(lambda l: l.transaction_value, filter(functools.partial(filter_relevant, transaction_type=u"D"), activity.disbursements)))
        #sum_forwardspends = sum(map(lambda l: l.transaction_value, filter(functools.partial(filter_relevant, transaction_type=u"C"), activity.finances)))
        sum_forwardspends = sum(map(lambda l: l.value, filter(functools.partial(filter_relevant, transaction_type=u"D"), activity.forwardspends)))

        pct = make_pct(sum_disbursements, sum_forwardspends)
        if (pct > 0) and (sum_forwardspends > 1000000):
            act = activity.as_jsonable_dict()
            act['sum_disbursements'] = "{:,.2f}".format(sum_disbursements),
            act['sum_forwardspends'] = "{:,.2f}".format(sum_forwardspends),
            act['disb_forwardspends'] = pct
            out.append(act)
    current_year, current_quarter = util.date_to_fy_fq(datetime.datetime.utcnow())
    start_of_fy = util.fq_fy_to_date(1, current_year, start_end='start')
    days_since_fy_begin = ((datetime.datetime.utcnow()-start_of_fy).days)
    progress_time = round(days_since_fy_begin/365.0*100.0, 2)
    return render_template(
        "reports/aid_disbursements.html",
        activities=out,
        progress_time=progress_time,
        days_since_fy_begin=days_since_fy_begin,
        fy_start_day=datetime.datetime.strftime(start_of_fy, "%d.%m.%Y"),
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
