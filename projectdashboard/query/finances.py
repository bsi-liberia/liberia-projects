import datetime

from flask_login import current_user

from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.lib import util
from projectdashboard.lib.util import MONTHS_QUARTERS, QUARTERS_MONTH_DAY
from projectdashboard.query import exchangerates as qexchangerates
from projectdashboard.query.activity_log import activity_updated


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")


def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")


def add_fund_source(data):
    fund_source = models.FundSource()
    fund_source.code = data["code"]
    fund_source.name = data["name"]
    fund_source.finance_type = data["finance_type"]
    db.session.add(fund_source)
    db.session.commit()
    return fund_source


def add_finances(activity_id, data):
    activity_finance = models.ActivityFinances()
    activity_finance.activity_id = activity_id
    classifications = data.get("classifications")
    data.pop("classifications")
    data["transaction_date"] = isostring_date(data["transaction_date"])
    activity_finance.currency_automatic = True
    activity_finance.currency_source, activity_finance.currency_rate, activity_finance.currency_value_date = qexchangerates.get_exchange_rate(
        data["transaction_date"], data.get("currency", "USD"))
    for key, value in data.items():
        setattr(activity_finance, key, value)
    _classifications = []
    for key, value in classifications.items():
        _c = models.ActivityFinancesCodelistCode()
        _c.codelist_id = key
        _c.codelist_code_id = value
        _classifications.append(_c)
    activity_finance.classifications = _classifications
    db.session.add(activity_finance)
    db.session.commit()

    activity_updated(activity_id,
         {
             "user_id": current_user.id,
             "mode": "add",
             "target": "ActivityFinances",
             "target_id": activity_finance.id,
             "old_value": None,
             "value": activity_finance.as_dict()
         }
     )
    return activity_finance


def update_finances_classification(data):
    check_finance = models.ActivityFinancesCodelistCode.query.filter_by(
        activityfinance_id=data["finances_id"],
        codelist_id=data["attr"]
    ).first()
    if not check_finance:
        return False
    old_value = check_finance.codelist_code_id
    check_finance.codelist_code_id = data["value"]
    db.session.add(check_finance)
    db.session.commit()

    activity_updated(data["activity_id"],
                     {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityFinancesCodelistCode",
        "target_id": check_finance.id,
        "old_value": {data["attr"]: old_value},
        "value": {data["attr"]: data["value"]}
    }
    )
    return models.ActivityFinances.query.filter_by(id=data["finances_id"]).first()


def delete_finances(activity_id, finances_id):
    print("Delete activity id {} finances id {}".format(activity_id, finances_id))
    check_finance = models.ActivityFinances.query.filter_by(
        activity_id=activity_id,
        id=finances_id
    ).first()
    if check_finance:
        old_value = check_finance.as_dict()
        db.session.delete(check_finance)
        db.session.commit()

        activity_updated(check_finance.activity_id,
            {
                "user_id": current_user.id,
                "mode": "delete",
                "target": "ActivityFinances",
                "target_id": old_value["id"],
                "old_value": old_value,
                "value": None
            }
        )
        return {"result": True}
    return False


def update_attr(data):
    finance = models.ActivityFinances.query.filter_by(
        id=data['finances_id']
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

    activity_updated(finance.activity_id,
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
    if start_date.year == end_date.year:  # They are the same
        for quarter in range(MONTHS_QUARTERS[start_date.month], MONTHS_QUARTERS[end_date.month]+1):
            periods.append((quarter, start_date.year))
    else:  # They are different
        # Do start year
        for quarter in range(MONTHS_QUARTERS[start_date.month], 5):
            periods.append((quarter, start_date.year))
        # Do in between year
        for year in range(start_date.year+1, end_date.year):
            for quarter in range(1, 5):
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
    forward_spend = models.ActivityForwardSpend.query.filter_by(
        activity_id=activity_id).all()
    existing_periods = list(map(lambda f: (
        util.MONTHS_QUARTERS[f.period_start_date.month],
        f.period_start_date.year), forward_spend))

    def filter_from_existing(required_period):
        return (required_period not in existing_periods)
    new_periods = list(filter(filter_from_existing, required_periods))
    forward_spends = create_forward_spends_from_periods(new_periods)
    return forward_spends


def create_or_update_forwardspend(activity_id, quarter, year, value, currency):
    # NB quarters are in calendar quarters, not Liberian fiscal quarters
    start_day, start_month = QUARTERS_MONTH_DAY[quarter]["start"]
    end_day, end_month = QUARTERS_MONTH_DAY[quarter]["end"]
    start_date = datetime.datetime(year, start_month, start_day).date()
    end_date = datetime.datetime(year, end_month, end_day).date()
    forward_spend = models.ActivityForwardSpend.query.filter_by(activity_id=activity_id,
                                                     period_start_date=start_date).first()
    if forward_spend:
        old_value = forward_spend.value
        forward_spend.value = value
        db.session.add(forward_spend)
        db.session.commit()
        activity_updated(forward_spend.activity_id,
            {
                "user_id": current_user.id,
                "mode": "update",
                "target": "ActivityForwardSpend",
                "target_id": forward_spend.id,
                "old_value": {"value": old_value},
                "value": {"value": value}
            }
        )
        return forward_spend
    else:
        forward_spend = models.ActivityForwardSpend()
        forward_spend.activity_id = activity_id
        forward_spend.value = value
        forward_spend.value_date = start_date
        forward_spend.value_currency = currency
        forward_spend.period_start_date = start_date
        forward_spend.period_end_date = end_date
        db.session.add(forward_spend)
        db.session.commit()
        activity_updated(forward_spend.activity_id,
            {
                "user_id": current_user.id,
                "mode": "add",
                "target": "ActivityForwardSpend",
                "target_id": forward_spend.id,
                "old_value": None,
                "value": forward_spend.as_dict()
            }
        )
        return forward_spend


def create_forward_spend(quarter, year, value, currency):
    # NB quarters are in calendar quarters, not Liberian fiscal quarters
    forward_spend = models.ActivityForwardSpend()
    forward_spend.value = value
    start_day, start_month = QUARTERS_MONTH_DAY[quarter]["start"]
    end_day, end_month = QUARTERS_MONTH_DAY[quarter]["end"]
    forward_spend.value_date = datetime.datetime(year, start_month, start_day)
    forward_spend.value_currency = currency
    forward_spend.period_start_date = datetime.datetime(year, start_month, start_day)
    forward_spend.period_end_date = datetime.datetime(year, end_month, end_day)
    return forward_spend


def create_forward_spends_from_periods(periods, value=0, currency="USD"):
    forwardspends = []
    if value > 0:
        value = round(value/len(periods), 2)
    for quarter, year in periods:
        forward_spend = create_forward_spend(quarter, year, value, currency)
        forwardspends.append(forward_spend)
    return forwardspends


def create_forward_spends(start_date, end_date, value=0, currency="USD"):
    forwardspends = []
    periods = create_periods(start_date, end_date)
    if value > 0:
        value = round(value/len(periods), 2)
    for quarter, year in periods:
        forward_spend = create_forward_spend(quarter, year, value, currency)
        forwardspends.append(forward_spend)
    return forwardspends


def update_fs_attr(data):
    forward_spend = models.ActivityForwardSpend.query.filter_by(
        id=data['id']
    ).first()
    old_value = forward_spend.value
    forward_spend.value = data['value']
    db.session.add(forward_spend)
    db.session.commit()

    activity_updated(forward_spend.activity_id,
        {
            "user_id": current_user.id,
            "mode": "update",
            "target": "ActivityForwardSpend",
            "target_id": forward_spend.id,
            "old_value": {"value": old_value},
            "value": {"value": data['value']}
        }
    )
    return True
