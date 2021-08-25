from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.lib import util
from projectdashboard.query import activity as qactivity
import datetime

START_QUARTERS = ['01-01', '04-01', '07-01', '10-01']
END_QUARTERS = ['03-31', '06-30', '09-30', '12-31']


def quarters_between(start_date, end_date):
    num_start = START_QUARTERS.index(start_date[5:10])
    num_end = END_QUARTERS.index(end_date[5:10])
    if num_end < num_start:
        return num_start+num_end+1
    return num_end-num_start+1


def validate_fiscalyears_input(fiscal_years):
    for i, item in enumerate(fiscal_years):
        # Check from is before to
        if item['start_date'] > item['end_date']: return False
        if i == 0: continue
        # Check from is after the previous item's to
        if item['start_date'] < fiscal_years[i-1]['end_date']: return False
        # Check start and end dates align with calendar quarters
        if item['start_date'][5:10] not in START_QUARTERS: return False
        if item['end_date'][5:10] not in END_QUARTERS: return False
    return True


def create_fiscal_year_choices(fiscal_years):
    for existing_fiscal_year_choice in models.FiscalYearChoice.query.all():
        db.session.delete(existing_fiscal_year_choice)
    db.session.commit()
    for fiscal_year in fiscal_years:
        fyc = models.FiscalYearChoice(
            start_date = util.isostring_date(fiscal_year['start_date']),
            end_date = util.isostring_date(fiscal_year['end_date']),
            num_quarters = quarters_between(fiscal_year['start_date'],
                fiscal_year['end_date'])
        )
        db.session.add(fyc)
    db.session.commit()


def make_fiscal_year_id(start_year, end_year, num_quarters):
    if start_year != end_year:
        return f"FY{start_year}/{end_year}"
    elif num_quarters != 4:
        return f"FY{start_year}(S)"
    else:
        return f"FY{start_year}"


def add_num_quarters(date, add_quarters, start_end="start"):
    if start_end=="start":
        target = START_QUARTERS
    if start_end=="end":
        target = END_QUARTERS
    qtr = target.index(date.isoformat()[5:10])
    qtr_plus_quarters = qtr+add_quarters
    if qtr_plus_quarters > 3:
        qtr_date = target[qtr_plus_quarters-4]
        qtr_year = date.year+1
        qtr_month, qtr_day = qtr_date.split("-")
    else:
        qtr_date = target[qtr_plus_quarters]
        qtr_year = date.year
        qtr_month, qtr_day = qtr_date.split("-")
    return datetime.date(qtr_year, int(qtr_month), int(qtr_day))


def add_quarters(start_date, num_quarters):
    start_qtr = START_QUARTERS.index(start_date.isoformat()[5:10])
    end_qtr_month, end_qtr_date = END_QUARTERS[start_qtr].split("-")
    end_date = datetime.date(start_date.year, int(end_qtr_month), int(end_qtr_date))
    return add_num_quarters(end_date, num_quarters-1, "end")


def create_fiscal_period_for_fiscal_year(fiscal_year, order, start_date, end_date):
    fiscal_period = models.FiscalPeriod()
    fiscal_period.id = f"{fiscal_year.id}Q{order}"
    fiscal_period.order = order
    fiscal_period.name = f"Q{order}"
    fiscal_period.start = start_date
    fiscal_period.end = end_date
    return fiscal_period


def create_fiscal_periods_for_fiscal_year(fiscal_year):
    fiscal_periods = []
    for order in range(1, fiscal_year.num_quarters+1):
        _start_date = add_num_quarters(fiscal_year.start, order-1, "start")
        _end_date = add_quarters(fiscal_year.start, order)
        fiscal_period = create_fiscal_period_for_fiscal_year(fiscal_year, order, _start_date, _end_date)
        fiscal_periods.append(fiscal_period)
    return fiscal_periods


def create_fiscal_years_for_choice(fiscal_year_choice, fiscal_years):
    # Add number of quarters.
    # If still less than the end date, continue
    start_date = fiscal_year_choice.start_date
    i = 0
    while True:
        fiscal_year_start_date = datetime.date(start_date.year+i, start_date.month, start_date.day)
        fiscal_year = models.FiscalYear()
        fiscal_year.start = fiscal_year_start_date
        fiscal_year.end = add_quarters(fiscal_year_start_date, fiscal_year_choice.num_quarters)
        fiscal_year.id = make_fiscal_year_id(fiscal_year_start_date.year, fiscal_year.end.year, fiscal_year_choice.num_quarters)
        fiscal_year.name = fiscal_year.id
        fiscal_year.num_quarters = fiscal_year_choice.num_quarters
        fiscal_year.fiscal_year_periods = create_fiscal_periods_for_fiscal_year(fiscal_year)
        fiscal_years.append(fiscal_year)
        db.session.merge(fiscal_year)
        i += 1
        if fiscal_year.end == fiscal_year_choice.end_date: break
    db.session.commit()
    return fiscal_years


def assign_financial_data_to_fiscal_year(fiscal_year_ids):
    fps = models.FiscalPeriod.query.filter(
            models.FiscalPeriod.fiscal_year_id.in_(fiscal_year_ids)
        ).order_by(
            models.FiscalPeriod.start
        ).all()
    fps_start = list(map(lambda fp: fp.start, fps))
    fps_end = list(map(lambda fp: fp.end, fps))
    fps_ids = list(map(lambda fp: fp.id, fps))
    # Get the first FiscalPeriod that is the same or greater than the finance.transaction_date
    # FiscalPeriod 2013-07-01
    # finance.transaction_date 2013-07-02 <== should be asssigned to above FP
    for finance in models.ActivityFinances.query.all():
        earliest_fps = [fp_date for fp_date in fps_start if fp_date <= finance.transaction_date]
        if len(earliest_fps) == 0:
            finance.fiscal_period_id = None
            continue
        fps_index = fps_start.index(max(earliest_fps))
        finance.fiscal_period_id = fps_ids[fps_index]
        db.session.add(finance)
    for forwardspend in models.ActivityForwardSpend.query.all():
        earliest_fps = [fp_date for fp_date in fps_start if fp_date <= forwardspend.period_start_date]
        if len(earliest_fps) == 0:
            forwardspend.fiscal_period_id = None
            continue
        fps_index = fps_start.index(max(earliest_fps))
        forwardspend.fiscal_period_id = fps_ids[fps_index]
        db.session.add(forwardspend)
    for counterpartfunding in models.ActivityCounterpartFunding.query.all():
        earliest_fps = [fp_date for fp_date in fps_start if fp_date <= counterpartfunding.required_date]
        if len(earliest_fps) == 0:
            counterpartfunding.fiscal_period_id = None
            continue
        fps_index = fps_start.index(max(earliest_fps))
        counterpartfunding.fiscal_period_id = fps_ids[fps_index]
        db.session.add(counterpartfunding)


def create_fiscal_years():
    """
    Reads from fiscal_year_choices table and creates new fiscal_years
    and fiscal_periods
    """
    fiscal_years = []
    for fiscal_year_choice in models.FiscalYearChoice.query.all():
        fiscal_years = create_fiscal_years_for_choice(fiscal_year_choice, fiscal_years)

    fiscal_year_ids = list(map(lambda fy: fy.id, fiscal_years))
    assign_financial_data_to_fiscal_year(fiscal_year_ids)

    for db_fiscal_year_period in models.FiscalPeriod.query.all():
        if db_fiscal_year_period.fiscal_year_id not in fiscal_year_ids:
            db.session.delete(db_fiscal_year_period)
    for db_fiscal_year in models.FiscalYear.query.all():
        if db_fiscal_year.id not in fiscal_year_ids:
            db.session.delete(db_fiscal_year)

    db.session.commit()


def process_fiscal_years(fiscal_years):
    sorted_fiscal_years = sorted(fiscal_years, key=lambda k: k['end_date'])
    valid = validate_fiscalyears_input(sorted_fiscal_years)
    if not valid:
        return False
    fiscal_year_choices = create_fiscal_year_choices(sorted_fiscal_years)
    fiscal_years = create_fiscal_years()
    return True
