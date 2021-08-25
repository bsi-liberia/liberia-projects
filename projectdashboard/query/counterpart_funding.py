from flask_login import current_user
import datetime
from projectdashboard import models
from projectdashboard.lib import util
from projectdashboard.extensions import db
from projectdashboard.query import activity as qactivity
from sqlalchemy import func


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")


def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")


def add_entry(activity_id, data):
    CF = models.ActivityCounterpartFunding()
    CF.activity_id = activity_id
    data["required_date"] = isostring_date(data["required_date"])
    for key, value in data.items():
        setattr(CF, key, value)
    db.session.add(CF)
    db.session.commit()

    qactivity.activity_updated(
        activity_id,
        {
            "user_id": current_user.id,
            "mode": "add",
            "target": "ActivityCounterpartFunding",
            "target_id": CF.id,
            "old_value": None,
            "value": CF.as_dict()
        }
    )
    return CF


def delete_entry(activity_id, counterpartfunding_id):
    checkCF = models.ActivityCounterpartFunding.query.filter_by(
        activity_id=activity_id,
        id=counterpartfunding_id
    ).first()
    if checkCF:
        old_value = checkCF.as_dict()
        db.session.delete(checkCF)
        db.session.commit()
        qactivity.activity_updated(
            checkCF.activity_id,
            {
                "user_id": current_user.id,
                "mode": "delete",
                "target": "ActivityCounterpartFunding",
                "target_id": old_value["id"],
                "old_value": old_value,
                "value": None
            }
        )
        return True
    return False

# Counterpart funding data


def update_entry(data):
    cf = models.ActivityCounterpartFunding.query.filter_by(
        id=data['id']
    ).first()
    old_value = getattr(cf, data['attr'])
    if data['attr'].endswith('date'):
        if data["value"] == "":
            data["value"] = None
        else:
            data['value'] = isostring_date(data['value'])
    elif data['attr'] == "required_value":
        if data['value'] == "":
            data['value'] = 0.0
    setattr(cf, data['attr'], data['value'])
    db.session.add(cf)
    db.session.commit()

    qactivity.activity_updated(
        cf.activity_id,
        {
            "user_id": current_user.id,
            "mode": "update",
            "target": "ActivityCounterpartFunding",
            "target_id": cf.id,
            "old_value": {data['attr']: old_value},
            "value": {data['attr']: data['value']}
        }
    )

    return cf


def create_or_update_counterpart_funding(activity_id, required_date, value):
    """
    Updates the value of required counterpart funding for a given `activity_id`
    and `required_date`.

    If the value is 0, then the row is deleted from the database.

    If there is no existing row, a new row is added to the database.

    If there is an existing row, that row is updated.
    """
    cf = models.ActivityCounterpartFunding.query.filter_by(
        activity_id=activity_id,
        required_date=required_date
    ).first()
    # If 0, we just remove the row from database
    if cf and value == 0:
        old_value = cf.as_dict()
        db.session.delete(cf)
        db.session.commit()
        qactivity.activity_updated(
            cf.activity_id,
            {
                "user_id": current_user.id,
                "mode": "delete",
                "target": "ActivityCounterpartFunding",
                "target_id": cf.id,
                "old_value": old_value,
                "value": None
            }
        )
        return True
    # If no existing row, we create one
    if not cf:
        cf = models.ActivityCounterpartFunding()
        cf.activity_id = activity_id
        cf.required_date = required_date
        mode = "add"
        old_value = None
    # There is an existing row, so we use it
    else:
        mode = "update"
        old_value = cf.as_dict()
    cf.required_value = value
    db.session.add(cf)
    db.session.commit()
    qactivity.activity_updated(
        cf.activity_id,
        {
            "user_id": current_user.id,
            "mode": mode,
            "target": "ActivityCounterpartFunding",
            "target_id": cf.id,
            "old_value": old_value,
            "value": cf.as_dict()
        }
    )
    return True


def annotate_activities_with_aggregates(fiscal_year):
    def FY_forwardspends_for_FY():
        result = db.session.query(
            models.ActivityForwardSpend.activity_id,
            func.sum(models.ActivityForwardSpend.value).label("value")
        ).join(models.FiscalPeriod
               ).join(models.FiscalYear
                      ).filter(models.FiscalYear.id == fiscal_year
                               ).group_by(
            models.ActivityForwardSpend.activity_id
        ).all()

        def filter_blank(row):
            return row.value > 0
        return filter(filter_blank, result)

    def FY_counterpart_funding_for_FY():
        result = db.session.query(
            models.ActivityCounterpartFunding.activity_id,
            func.sum(models.ActivityCounterpartFunding.required_value).label(
                "value")
        ).join(models.FiscalPeriod
               ).join(models.FiscalYear
                      ).filter(models.FiscalYear.id == fiscal_year
                               ).group_by(
            models.ActivityCounterpartFunding.activity_id
        ).all()

        def filter_blank(row):
            return row.value > 0
        return filter(filter_blank, result)

    fy_forwardspends = dict(FY_forwardspends_for_FY())
    fy_counterpart_funding = dict(FY_counterpart_funding_for_FY())

    activities = models.Activity.query.filter(
        models.Activity.id.in_(
            list(fy_forwardspends.keys())+list(fy_counterpart_funding.keys()))
    ).all()

    def annotate_aggs(activity):
        activity._fy_forwardspends = fy_forwardspends.get(
            activity.id, 0.00)
        activity._fy_counterpart_funding = fy_counterpart_funding.get(
            activity.id, 0.00)
        return activity

    return list(map(lambda activity: annotate_aggs(activity), activities))
