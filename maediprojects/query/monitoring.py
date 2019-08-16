from maediprojects import models
from maediprojects.extensions import db
from maediprojects.lib import util
import sqlalchemy as sa
from sqlalchemy import func, case

def fwddata_query(current_previous="current"):
    return db.session.query(
            func.sum(models.ActivityForwardSpend.value).label("value"),
            models.Activity.reporting_org_id
        ).join(
            models.Activity
        ).filter(
            models.ActivityForwardSpend.value != 0
        ).filter(
            models.ActivityForwardSpend.period_start_date >= util.FY(current_previous).date("start")
        ).filter(
            models.ActivityForwardSpend.period_end_date <= util.FY(current_previous).date("end")
        ).group_by(models.Activity.reporting_org_id
        ).order_by(models.Activity.reporting_org_id.desc()
        ).all()


def fydata_query(fiscalyear_modifier, _transaction_types=[u"D", u"E"], current_previous="current"):
    if current_previous != "todate":
        since = util.FY(current_previous).date("start")
        until = util.FY(current_previous).date("end")
    else:
        since = util.Last4Quarters().start()
        until = util.Last4Quarters().end()
    return db.session.query(
            func.sum(models.ActivityFinances.transaction_value).label("value"),
            models.Activity.reporting_org_id,
            case(
                [
                    (func.STRFTIME('%m', func.DATE(models.ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('01','02','03')), 'Q1'),
                    (func.STRFTIME('%m', func.DATE(models.ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('04','05','06')), 'Q2'),
                    (func.STRFTIME('%m', func.DATE(models.ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('07','08','09')), 'Q3'),
                    (func.STRFTIME('%m', func.DATE(models.ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('10','11','12')), 'Q4'),
                ]
            ).label("fiscal_quarter")
        ).join(models.Activity
        ).filter(
            models.ActivityFinances.transaction_value != 0,
            models.ActivityFinances.transaction_type.in_(_transaction_types)
        ).filter(
            models.ActivityFinances.transaction_date >= since
        ).filter(
            models.ActivityFinances.transaction_date <= until
        ).group_by("fiscal_quarter"
        ).group_by(models.Activity.reporting_org_id
        ).order_by(models.Activity.reporting_org_id.desc()
        ).all()


def forwardspends_ros(current_previous="current"):
    forwardspends = fwddata_query(current_previous)
    return dict(map(lambda ro: (ro.reporting_org_id, round(ro.value)), forwardspends))


def fydata_ros(current_previous="current"):
    disbursements = fydata_query(6, [u"D", u"E"], current_previous)
    return dict(map(lambda ro: ((ro.reporting_org_id, ro.fiscal_quarter), round(ro.value)), disbursements))
