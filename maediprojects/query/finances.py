from maediprojects import db, models
from sqlalchemy import *
import datetime

def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")

def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")

def add_finances(activity_id, data):
    aF = models.ActivityFinances()
    aF.activity_id = activity_id
    #aF.transaction_date = data["transaction_date"]
    aF.transaction_type = data["transaction_type"]
    #aF.transaction_value = data["transaction_value"]
    #aF.transaction_description = data["transaction_description"]
    db.session.add(aF)
    db.session.commit()
    return aF.id

def delete_finances(activity_id, finances_id):
    checkF = models.ActivityFinances.query.filter_by(
        activity_id = activity_id,
        id = finances_id
    ).first()
    if checkF:
        db.session.delete(checkF)
        db.session.commit()
        return True
    return False

def update_attr(data):
    finance = models.ActivityFinances.query.filter_by(
        id = data['finances_id']
    ).first()
    if data['attr'].endswith('date'):
        if data["value"] == "": 
            data["value"] = None
        else:
            data['value'] = isostring_date(data['value'])
    setattr(finance, data['attr'], data['value'])
    db.session.add(finance)
    db.session.commit()
    return True
