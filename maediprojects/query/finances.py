import datetime

from flask_login import current_user
from sqlalchemy import *

from maediprojects import models
from maediprojects.extensions import db
from maediprojects.lib import util
from maediprojects.lib.util import MONTHS_QUARTERS, QUARTERS_MONTH_DAY
from maediprojects.query import exchangerates as qexchangerates
import activity as qactivity


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")

def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")

def add_finances(activity_id, data):
    aF = models.ActivityFinances()
    aF.activity_id = activity_id
    classifications = data.get("classifications")
    data.pop("classifications")
    data["transaction_date"] = isostring_date(data["transaction_date"])
    aF.currency_automatic=True
    aF.currency_source, aF.currency_rate, aF.currency_value_date = qexchangerates.get_exchange_rate(
        data["transaction_date"], data.get("currency", u"USD"))
    for key, value in data.items():
        setattr(aF, key, value)
    _classifications = []
    for key, value in classifications.items():
        _c = models.ActivityFinancesCodelistCode()
        _c.codelist_id = key
        _c.codelist_code_id = value
        _classifications.append(_c)
    aF.classifications = _classifications
    db.session.add(aF)
    db.session.commit()

    qactivity.activity_updated(activity_id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "ActivityFinances",
        "target_id": aF.id,
        "old_value": None,
        "value": aF.as_dict()
        }
        )
    return aF

def update_finances_classification(data):
    checkF = models.ActivityFinancesCodelistCode.query.filter_by(
        activityfinance_id = data["finances_id"],
        codelist_id = data["attr"]
    ).first()
    if not checkF: return False
    old_value = checkF.codelist_code_id
    checkF.codelist_code_id = data["value"]
    db.session.add(checkF)
    db.session.commit()

    qactivity.activity_updated(data["activity_id"],
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityFinancesCodelistCode",
        "target_id": checkF.id,
        "old_value": {data["attr"]: old_value},
        "value": {data["attr"]: data["value"]}
        }
        )
    return models.ActivityFinances.query.filter_by(id=data["finances_id"]).first()

def delete_finances(activity_id, finances_id):
    print "Delete activity id {} finances id {}".format(activity_id, finances_id)
    checkF = models.ActivityFinances.query.filter_by(
        activity_id = activity_id,
        id = finances_id
    ).first()
    if checkF:
        old_value = checkF.as_dict()
        db.session.delete(checkF)
        db.session.commit()
        print "Return True"

        qactivity.activity_updated(checkF.activity_id,
            {
            "user_id": current_user.id,
            "mode": "delete",
            "target": "ActivityFinances",
            "target_id": old_value["id"],
            "old_value": old_value,
            "value": None
            }
            )
        return True
    print "Return False"
    return False

def update_attr(data):
    finance = models.ActivityFinances.query.filter_by(
        id = data['finances_id']
    ).first()

    old_value = getattr(finance, data['attr'])

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

    qactivity.activity_updated(finance.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityFinances",
        "target_id": finance.id,
        "old_value": {data['attr']: old_value},
        "value": {data['attr']: data['value']}
        }
        )

    return finance

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

def create_missing_forward_spends(from_date, to_date, activity_id):
    # NB quarters here are in calendar quarters, not Liberian fiscal quarters
    def _switch_round(year_quarter):
        return year_quarter[1], year_quarter[0]

    required_periods = create_periods(from_date, to_date)
    fs = models.ActivityForwardSpend.query.filter_by(activity_id=activity_id).all()
    existing_periods = list(map(lambda f: (
        util.MONTHS_QUARTERS[f.period_start_date.month],
        f.period_start_date.year), fs))

    def filter_from_existing(required_period):
        return (required_period not in existing_periods)
    new_periods = filter(filter_from_existing, required_periods)
    forward_spends = create_forward_spends_from_periods(new_periods)
    return forward_spends

def create_or_update_forwardspend(activity_id, quarter, year, value, currency):
    # NB quarters are in calendar quarters, not Liberian fiscal quarters
    start_day, start_month = QUARTERS_MONTH_DAY[quarter]["start"]
    end_day, end_month = QUARTERS_MONTH_DAY[quarter]["end"]
    start_date = datetime.datetime(year, start_month, start_day).date()
    end_date = datetime.datetime(year, end_month, end_day).date()
    fs = models.ActivityForwardSpend.query.filter_by(activity_id=activity_id,
        period_start_date=start_date).first()
    if fs:
        fs.value = value
        db.session.add(fs)
        db.session.commit()
        return fs
    else:
        fs = models.ActivityForwardSpend()
        fs.activity_id = activity_id
        fs.value = value
        fs.value_date = start_date
        fs.value_currency = currency
        fs.period_start_date = start_date
        fs.period_end_date = end_date
        db.session.add(fs)
        db.session.commit()
        return fs

def create_forward_spend(quarter, year, value, currency):
    # NB quarters are in calendar quarters, not Liberian fiscal quarters
    fs = models.ActivityForwardSpend()
    fs.value = value
    start_day, start_month = QUARTERS_MONTH_DAY[quarter]["start"]
    end_day, end_month = QUARTERS_MONTH_DAY[quarter]["end"]
    fs.value_date = datetime.datetime(year, start_month, start_day)
    fs.value_currency = currency
    fs.period_start_date = datetime.datetime(year, start_month, start_day)
    fs.period_end_date = datetime.datetime(year, end_month, end_day)
    return fs

def create_forward_spends_from_periods(periods, value=0, currency=u"USD"):
    forwardspends = []
    if value>0: value = round(value/len(periods), 2)
    for quarter, year in periods:
        fs = create_forward_spend(quarter, year, value, currency)
        forwardspends.append(fs)
    return forwardspends

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
