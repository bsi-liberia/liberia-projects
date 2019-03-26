from flask_login import current_user
from sqlalchemy import *
import datetime
from maediprojects import db, models
from maediprojects.lib import util
from maediprojects.lib.util import MONTHS_QUARTERS, QUARTERS_MONTH_DAY
import activity as qactivity

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

    qactivity.activity_updated(activity_id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "ActivityCounterpartFunding",
        "target_id": CF.id,
        "old_value": None,
        "value": CF.as_dict()
        }
        )
    return CF.id

def delete_entry(activity_id, counterpartfunding_id):
    print "Delete activity id {} counterpart funding id {}".format(activity_id, counterpartfunding_id)
    checkCF = models.ActivityCounterpartFunding.query.filter_by(
        activity_id = activity_id,
        id = counterpartfunding_id
    ).first()
    if checkCF:
        old_value = checkCF.as_dict()
        db.session.delete(checkCF)
        db.session.commit()
        print "Return True"

        qactivity.activity_updated(checkCF.activity_id,
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
    print "Return False"
    return False

# Counterpart funding data
def update_entry(data):
    cf = models.ActivityCounterpartFunding.query.filter_by(
        id = data['id']
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

    qactivity.activity_updated(cf.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityCounterpartFunding",
        "target_id": cf.id,
        "old_value": {data['attr']: old_value},
        "value": {data['attr']: data['value']}
        }
        )

    return True
