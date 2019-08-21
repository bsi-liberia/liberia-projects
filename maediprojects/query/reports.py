from maediprojects import models
from maediprojects.extensions import db
from maediprojects.lib import util
from flask import url_for
import sqlalchemy as sa
from sqlalchemy import func, case
import datetime


def make_forwardspends_disbursements_data(fiscal_year, forwardspends_over=1000000,
        domestic_external="external"):
    year_end = util.fq_fy_to_date(4, fiscal_year, "end").date()
    year_start = util.fq_fy_to_date(1, fiscal_year, "start").date()

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

    disbursements = dict(map(lambda a: (a.id, a), db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("sum_disbursements"),
        models.Activity.id
        ).join(models.Activity, models.Activity.id == models.ActivityFinances.activity_id
        ).filter(
            models.ActivityFinances.transaction_date <= year_end
        ).filter(
            models.ActivityFinances.transaction_date >= year_start
        ).filter(
            models.ActivityFinances.transaction_type == u'D'
        ).group_by(
            models.Activity.id
        ).all()))

    def make_pct(value1, value2):
        try:
            return round((float(value1)/float(value2))*100.0)
        except Exception:
            return None

    def _make_activity_data(out=[]):
        for activity in forwardspends:
            act = dict(zip(activity.keys(), activity))
            act["url"] = url_for('activities.activity', activity_id=activity.id)
            if disbursements.get(activity.id):
                act["sum_disbursements"] = disbursements[activity.id].sum_disbursements
                act["pct"] = make_pct(act["sum_disbursements"], activity.sum_forwardspends)
            else:
                act["sum_disbursements"] = 0.00
                act["pct"] = 0.00
            out.append(act)
        return out
    return _make_activity_data()


def make_appropriations_disbursements_data(fiscal_year,
        appropriations_over=0, domestic_external='domestic'):
    year_start = util.fq_fy_to_date(1, fiscal_year, "start").date()
    year_end = util.fq_fy_to_date(4, fiscal_year, "end").date()

    appropriations = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("sum_appropriations"),
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
            models.ActivityFinances.transaction_type == u'C'
        ).group_by(
            models.Activity.id,
            models.Activity.title,
            models.Activity.reporting_org_id,
            models.Organisation.name
        ).order_by(func.sum(models.ActivityFinances.transaction_value).desc()
        ).all()

    disbursements = dict(map(lambda a: (a.id, a), db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("sum_disbursements"),
        models.Activity.id
        ).join(models.Activity, models.Activity.id == models.ActivityFinances.activity_id
        ).filter(
            models.Activity.domestic_external == domestic_external
        ).filter(
            models.ActivityFinances.transaction_date <= year_end
        ).filter(
            models.ActivityFinances.transaction_date >= year_start
        ).filter(
            models.ActivityFinances.transaction_type == u'D'
        ).group_by(
            models.Activity.id
        ).all()))

    def make_pct(value1, value2):
        try:
            return round((float(value1)/float(value2))*100.0)
        except Exception:
            return None

    def _make_activity_data(out=[]):
        for activity in appropriations:
            act = dict(zip(activity.keys(), activity))
            act["url"] = url_for('activities.activity', activity_id=activity.id)
            if disbursements.get(activity.id):
                act["sum_disbursements"] = disbursements[activity.id].sum_disbursements
                act["pct"] = make_pct(act["sum_disbursements"], activity.sum_appropriations)
            else:
                act["sum_disbursements"] = 0.00
                act["pct"] = 0.00
            out.append(act)
        return out
    return _make_activity_data()