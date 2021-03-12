from maediprojects import models
from maediprojects.extensions import db
from maediprojects.lib import util
import sqlalchemy as sa
from sqlalchemy import func, case
import datetime


def make_start_end_from_fy(fiscal_year):
    year_end = util.fq_fy_to_date(4, fiscal_year, "end").date()
    year_start = util.fq_fy_to_date(1, fiscal_year, "start").date()
    return year_start, year_end


def make_pct(value1, value2):
    try:
        return round((float(value1)/float(value2))*100.0)
    except Exception:
        return None


def _make_activity_data(denominator_list, numerator_dict, denominator_label, numerator_label):
    out = []
    for activity in denominator_list:
        act = dict(zip(activity.keys(), activity))
        if numerator_dict.get(activity.id):
            act[numerator_label] = numerator_dict[activity.id]
            act["pct"] = make_pct(act[numerator_label], getattr(activity, denominator_label))
        else:
            act[numerator_label] = 0.00
            act["pct"] = 0.00
        out.append(act)
    return out


def sum_forwardspends(fiscal_year, forwardspends_over, domestic_external, activity_detail=True):
    year_start, year_end = make_start_end_from_fy(fiscal_year)
    forwardspends = db.session.query(
        func.sum(models.ActivityForwardSpend.value).label("sum_forwardspends"),
        models.Activity.id,
        models.Activity.title,
        models.Activity.reporting_org_id,
        models.Organisation.name.label("reporting_org_name")
        ).join(models.Activity, models.Activity.id == models.ActivityForwardSpend.activity_id
        ).join(models.Organisation, models.Activity.reporting_org
        ).filter(
            models.Activity.domestic_external == domestic_external
        ).filter(
            models.ActivityForwardSpend.period_end_date <= year_end
        ).filter(
            models.ActivityForwardSpend.period_end_date >= year_start
        ).having(
            func.sum(models.ActivityForwardSpend.value) > forwardspends_over
        ).group_by(
            models.Activity.id,
            models.Activity.title,
            models.Activity.reporting_org_id,
            models.Organisation.name
        ).order_by(func.sum(models.ActivityForwardSpend.value).desc()
        ).all()
    return forwardspends


def sum_transactions(fiscal_year, sum_over, domestic_external, label, transaction_type):
    year_start, year_end = make_start_end_from_fy(fiscal_year)
    disbursements = dict(map(lambda a: (a.id, getattr(a, label)), db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label(label),
        models.Activity.id
        ).join(models.Activity, models.Activity.id == models.ActivityFinances.activity_id
        ).filter(
            models.ActivityFinances.transaction_date <= year_end
        ).filter(
            models.ActivityFinances.transaction_date >= year_start
        ).filter(
            models.ActivityFinances.transaction_type == transaction_type
        ).filter(
            models.Activity.domestic_external == domestic_external
        ).group_by(
            models.Activity.id
        ).all()))
    return disbursements


def sum_transactions_detail(fiscal_year, sum_over, domestic_external, label, transaction_type):
    year_start, year_end = make_start_end_from_fy(fiscal_year)
    appropriations = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label(label),
        models.Activity.id,
        models.Activity.title,
        models.Activity.reporting_org_id,
        models.Organisation.name.label("reporting_org_name")
        ).join(models.Activity, models.Activity.id == models.ActivityFinances.activity_id
        ).join(models.Organisation, models.Activity.reporting_org
        ).filter(
            models.Activity.domestic_external == domestic_external
        ).filter(
            models.ActivityFinances.transaction_date >= year_start
        ).filter(
            models.ActivityFinances.transaction_date <= year_end
        ).filter(
            models.ActivityFinances.transaction_type == transaction_type
        ).group_by(
            models.Activity.id,
            models.Activity.title,
            models.Activity.reporting_org_id,
            models.Organisation.name
        ).order_by(func.sum(models.ActivityFinances.transaction_value).desc()
        ).all()
    return appropriations

def make_forwardspends_disbursements_data(fiscal_year, forwardspends_over=1000000,
        domestic_external="external"):
    forwardspends = sum_forwardspends(fiscal_year, forwardspends_over,
        domestic_external, activity_detail=True)
    label = 'sum_disbursements'
    disbursements = sum_transactions(fiscal_year, 0, domestic_external, label, 'D')
    return _make_activity_data(forwardspends, disbursements,
        'sum_forwardspends', label)


def make_appropriations_disbursements_data(fiscal_year,
        appropriations_over=0, domestic_external='domestic'):
    appropriations = sum_transactions_detail(fiscal_year, appropriations_over,
        domestic_external, 'sum_appropriations', 'C')
    label = 'sum_disbursements'
    allotments = sum_transactions(fiscal_year, 0, domestic_external, 'sum_allotments', '99-A')
    disbursements = sum_transactions(fiscal_year, 0, domestic_external, label, 'D')
    made_data = _make_activity_data(appropriations, disbursements,
        'sum_appropriations', label)
    def annotate_activity(activity, allotments):
        activity['sum_allotments'] = allotments.get(activity['id'], 0.00)
        return activity
    return [annotate_activity(activity, allotments) for activity in made_data]
