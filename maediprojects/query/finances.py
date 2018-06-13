from maediprojects import db, models
from sqlalchemy import *
import datetime
from maediprojects.lib.util import MONTHS_QUARTERS, QUARTERS_MONTH_DAY

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
    elif data['attr'] == "transaction_value":
        if data['value'] == "":
            data['value'] = 0.0
    setattr(finance, data['attr'], data['value'])
    db.session.add(finance)
    db.session.commit()
    return True

# Forward spend data

def create_periods(start_date, end_date):
    periods = []
    if start_date.year == end_date.year:  ## They are the same
        for quarter in range(MONTHS_QUARTERS[start_date.month], MONTHS_QUARTERS[end_date.month]+1):
            periods.append((quarter, start_date.year))
    else: ## They are different
        # Do start year
        for quarter in range(MONTHS_QUARTERS[start_date.month], 5):
            periods.append((quarter, start_date.year))
        # Do in between year
        for year in range(start_date.year+1, end_date.year):
            for quarter in range(1,5):
                periods.append((quarter, year))
        # Do end year
        for quarter in range(1, MONTHS_QUARTERS[end_date.month]+1):
            periods.append((quarter, end_date.year))
    return periods

def create_forward_spend(quarter, year, value, currency):
    fs = models.ActivityForwardSpend()
    fs.value = value
    start_day, start_month = QUARTERS_MONTH_DAY[quarter]["start"]
    end_day, end_month = QUARTERS_MONTH_DAY[quarter]["end"]
    fs.value_date = datetime.datetime(year, start_month, start_day)
    fs.value_currency = currency
    fs.period_start_date = datetime.datetime(year, start_month, start_day)
    fs.period_end_date = datetime.datetime(year, end_month, end_day)
    return fs

def create_forward_spends(start_date, end_date, value=0, currency=u"USD"):
    forwardspends = []
    periods = create_periods(start_date, end_date)
    if value>0: value = round(value/len(periods), 2)
    for quarter, year in periods:
        fs = create_forward_spend(quarter, year, value, currency)
        forwardspends.append(fs)
    return forwardspends

def update_fs_attr(data):
    fs = models.ActivityForwardSpend.query.filter_by(
        id = data['id']
    ).first()
    fs.value = data['value']
    db.session.add(fs)
    db.session.commit()
    return True    
