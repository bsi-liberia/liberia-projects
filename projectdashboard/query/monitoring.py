from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.lib import util
import sqlalchemy as sa
from sqlalchemy import func, case
import datetime


def response_statuses():
    return models.Response.query.all()


def generate_data_collection_calendar():
    #FIXME query database instead of hardocded calendar
    current_year = datetime.datetime.now().year
    data_collection_calendar=[
        {
            "iso_date": datetime.date(current_year,1,15),
            "date": datetime.datetime.strftime(datetime.date(current_year,1,15), "%B %d"),
            "data_request": "Disbursement data for Q2 of the current FY (October-December)"
        },
        {   "iso_date": datetime.date(current_year,2,15),
            "date": datetime.datetime.strftime(datetime.date(current_year,2,15), "%B %d"),
            "data_request": "Forward disbursement projections: for the next 3 FYs"
        },
        {
            "iso_date": datetime.date(current_year,4,15),
            "date": datetime.datetime.strftime(datetime.date(current_year,4,15), "%B %d"),
            "data_request": "Disbursement data for Q3 of the current FY (January-March)"
        },
        {   "iso_date": datetime.date(current_year,7,15),
            "date": datetime.datetime.strftime(datetime.date(current_year,7,15), "%B %d"),
            "data_request": "Disbursement data for Q4 of the previous FY (April-June)"
        },
        {
            "iso_date": datetime.date(current_year,10,15),
            "date": datetime.datetime.strftime(datetime.date(current_year,10,15), "%B %d"),
            "data_request": "Disbursement data for Q1 of the current FY (July-September)"
        }
    ]
    def filter_passed(obj):
        return datetime.datetime.now().date() > obj["iso_date"]

    date_to_highlight = max(list(map(lambda o: o["iso_date"], filter(filter_passed, data_collection_calendar))))

    def check_row_variant(c):
        if c["iso_date"] == date_to_highlight:
            c["_rowVariant"] = "warning"
        return c

    return list(map(lambda c: check_row_variant(c), data_collection_calendar))


def update_organisation_response(data):
    orgresp = models.OrganisationResponse.query.filter_by(
        organisation_id = data['organisation_id'],
        fyfq = data['fyfq']).first()
    if orgresp and (data["response_id"] == None):
        db.session.delete(orgresp)
        db.session.commit()
        return True
    if not orgresp:
        orgresp = models.OrganisationResponse()
    orgresp.fyfq = data['fyfq']
    orgresp.organisation_id = data['organisation_id']
    orgresp.response_id = data['response_id']
    db.session.add(orgresp)
    db.session.commit()
    return True


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
