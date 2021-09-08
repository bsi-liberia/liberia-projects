import datetime
import re
import collections
from projectdashboard import models

ALLOWED_YEARS = range(2013, datetime.datetime.utcnow().year+3)

MONTHS_QUARTERS = {
    1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4,
    11: 4, 12: 4
}

QUARTERS_MONTH_DAY = {
    1: {"start": (1, 1), "end": (31, 3)},
    2: {"start": (1, 4), "end": (30, 6)},
    3: {"start": (1, 7), "end": (30, 9)},
    4: {"start": (1, 10), "end": (31, 12)}
}

LR_MONTHS_QUARTERS = {
    1: 3, 2: 3, 3: 3, 4: 4, 5: 4, 6: 4, 7: 1, 8: 1, 9: 1, 10: 2,
    11: 2, 12: 2
}

LR_QUARTERS_MONTH_DAY = {
    1: {"start": (1, 7), "end": (30, 9)},
    2: {"start": (1, 10), "end": (31, 12)},
    3: {"start": (1, 1), "end": (31, 3)},
    4: {"start": (1, 4), "end": (30, 6)}
}

LR_PERIODS_MONTH_DAY = {
    "M7": {"start": (1, 1), "end": (31, 1)},
    "M8": {"start": (1, 2), "end": (28, 2)},
    "M9": {"start": (1, 3), "end": (31, 3)},
    "M10": {"start": (1, 4), "end": (30, 4)},
    "M11": {"start": (1, 5), "end": (31, 5)},
    "M12": {"start": (1, 6), "end": (30, 6)},
    "M13": {"start": (1, 6), "end": (30, 6)},
    "M0": {"start": (1, 7), "end": (31, 7)},
    "M1": {"start": (1, 7), "end": (31, 7)},
    "M2": {"start": (1, 8), "end": (31, 8)},
    "M3": {"start": (1, 9), "end": (30, 9)},
    "M4": {"start": (1, 10), "end": (31, 10)},
    "M5": {"start": (1, 11), "end": (30, 11)},
    "M6": {"start": (1, 12), "end": (31, 12)}
}

LR_QUARTERS_CAL_QUARTERS = {
    1: 3,
    2: 4,
    3: 1,
    4: 2
}


def lr_quarter_to_cal_quarter(_fy, _fq):
    if _fq in (3, 4):
        year = _fy+1
    else:
        year = _fy
    quarter = LR_QUARTERS_CAL_QUARTERS[_fq]
    return year, quarter


def fp_fy_to_date(fp, fy, start_end='start'):
    """Convert from LR FP, FY to real date."""
    if fp in ("M7", "M8", "M9", "M10", "M11", "M12", "M13"):
        year = fy+1
    else:
        year = fy
    day, month = LR_PERIODS_MONTH_DAY[fp][start_end]
    return datetime.datetime(year, month, day)


def fq_fy_to_date(fq, fy, start_end='start', calendar_year=False):
    """
    Convert from Liberian FQ, FY (default) or calendar
    FQ, FY to real date
    """
    if calendar_year:
        """Convert from calendar year FQ, FY to real data."""
        day, month = QUARTERS_MONTH_DAY[fq][start_end]
        year = fy
        return datetime.datetime(year, month, day)
    else:
        fp = models.FiscalPeriod.query.filter_by(
            fiscal_year_id=f'FY{fy}',
            name=f'Q{fq}').first()
        if start_end == 'start':
            return fp.start
        return fp.end


def date_to_fy_fq_calendar_year(date):
    quarter = MONTHS_QUARTERS[date.month]
    return date.year, quarter


def date_to_fy_fq(date):
    quarter = LR_MONTHS_QUARTERS[date.month]
    # Q3 and Q4 (Jan-Jun) are FY of previous year
    if quarter in (3, 4):
        year = date.year-1
    else:
        year = date.year
    return year, quarter


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    if value == "":
        return None
    return datetime.datetime.strptime(value[0:10], "%Y-%m-%d")


def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")


def subtract_one_quarter(from_year, from_quarter):
    if from_quarter > 1:
        return from_year, from_quarter-1
    else:
        return from_year-1, 4


def add_one_quarter(from_year, from_quarter):
    if from_quarter < 4:
        return from_year, from_quarter+1
    else:
        return from_year+1, 1


def available_fys_forward(num_years=4):
    now = datetime.datetime.utcnow()
    cutoff_date = datetime.date(now.year+num_years, now.month, now.day)
    db_fys = models.FiscalYear.query.filter(
        models.FiscalYear.start > now,
        models.FiscalYear.end <= cutoff_date
    ).order_by(models.FiscalYear.end
               ).all()
    return [db_fy.id for db_fy in db_fys if db_fy.end <= cutoff_date]


def available_fys(num_years=4):
    now = datetime.datetime.utcnow()
    cutoff_date = datetime.date(now.year+num_years, now.month, now.day)
    db_fys = models.FiscalYear.query.filter(
        models.FiscalYear.end <= cutoff_date
    ).order_by(models.FiscalYear.end
               ).all()
    return [db_fy.id for db_fy in db_fys if db_fy.end <= cutoff_date]


def available_fy_fqs():
    now = datetime.datetime.utcnow()
    cutoff_date = datetime.date(now.year+3, now.month, now.day)
    db_fys_fps = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.end <= cutoff_date
    ).order_by(
        models.FiscalPeriod.end
    ).all()
    return ["{} {} (D)".format(fp.fiscal_year_id, fp.name) for fp in db_fys_fps]


def current_fy_fq():
    fp = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.start <= datetime.datetime.utcnow(),
        models.FiscalPeriod.end >= datetime.datetime.utcnow()
    ).first()
    return "{} {} (D)".format(fp.fiscal_year_id, fp.name)


def previous_fy_fq():
    fp = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.end < datetime.datetime.utcnow()
    ).order_by(
        models.FiscalPeriod.end.desc()
    ).first()
    return "{} {} (D)".format(fp.fiscal_year_id, fp.name)


def previous_fy_fq_date(start_end="end"):
    fp = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.end < datetime.datetime.utcnow()
    ).order_by(
        models.FiscalPeriod.end.desc()
    ).first()
    if start_end == 'start':
        return fp.start
    return fp.end


class Last4Quarters:
    def start(self):
        """The start of the quarter one year ago."""
        return self.db_quarters[0].start

    def end(self):
        """End of the previous quarter from today: because we don't want to include
        the current incomplete quarter"""
        return self.db_quarters[3].end

    def list_of_quarters(self):
        out = collections.OrderedDict()
        for i in range(4):
            out["Q{}".format(i+1)] = "{}".format(self.db_quarters[i].id)
        return out

    def __init__(self):
        self.FY = FY("current")
        self.db_quarters = sorted(models.FiscalPeriod.query.filter(
            models.FiscalPeriod.end < datetime.datetime.utcnow()
        ).order_by(models.FiscalPeriod.start.desc()
                   ).limit(4).all(), key=lambda item: item.start)


class FP:
    def fy_to_date(self, fy, start_end):
        return fq_fy_to_date({"start": 1, "end": 4}[start_end], fy, start_end)

    def fy_fy(self):
        year, quarter = self.numeric()
        return self.fiscal_period.fiscal_year.name

    def fy(self):
        year, quarter = date_to_fy_fq(datetime.datetime.utcnow())
        return "{}".format(year)

    def numeric(self):
        fp = models.FiscalPeriod.query.filter(
            models.FiscalPeriod.start <= self.current_date,
            models.FiscalPeriod.end >= self.current_date
        ).first()
        self.fiscal_period = fp
        year = fp.fiscal_year.name
        quarter = fp.name
        return year, quarter

    def date(self, start_end="end"):
        fy, fq = self.numeric()
        if start_end == "start":
            return self.fiscal_period.start
        return self.fiscal_period.end

    def __init__(self, current_previous):
        if current_previous == "current":
            self.current_date = datetime.datetime.utcnow()
        elif current_previous == "previous":
            self.current_date = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        elif current_previous == "next":
            self.current_date = datetime.datetime.utcnow() + datetime.timedelta(days=365)
        else:
            raise Exception


class FY:
    def fy_fy(self):
        return self.fiscal_year.name

    def date(self, start_end="end"):
        if start_end == "start":
            return self.fiscal_year.start
        return self.fiscal_year.end

    def __init__(self, current_previous):
        if current_previous == "current":
            self.current_date = datetime.datetime.utcnow()
        elif current_previous == "previous":
            self.current_date = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        elif current_previous == "next":
            self.current_date = datetime.datetime.utcnow() + datetime.timedelta(days=365)
        else:
            raise Exception
        self.fiscal_year = models.FiscalYear.query.filter(
            models.FiscalYear.start <= self.current_date,
            models.FiscalYear.end >= self.current_date
        ).first()


def available_fy_fqs_as_dict():
    return [{'value': fyfqstring,
             'text': column_data_to_string(fyfqstring),
             'selected': previous_fy_fq() == fyfqstring
             } for fyfqstring in available_fy_fqs()]


def available_fys_as_dict():
    return [{'value': fyfqstring,
             'text': fyfqstring
             } for fyfqstring in available_fys()]


def get_data_from_fy_fq_string(fy_fq_string):
    pattern = r"FY(\d*) Q(\d)"
    result = re.match(pattern, column_name).groups()
    return (result[1], result[0])


def fy_fq_string_to_date(fy_fq_string, start_end='start'):
    year, quarter = get_data_from_fy_fq_string(fy_fq_string)
    return fq_fy_to_date(quarter, year, start_end)


def get_data_from_header(column_name):
    pattern = r"FY(\S*) Q(\d) \(D\)"
    result = re.match(pattern, column_name).groups()
    return (result[1], result[0])


def fys_in_date_range(start_date, end_date):
    """Returns all the fiscal years between the start and end dates"""
    fys = models.FiscalYear.query.filter(
        models.FiscalYear.start >= start_date
    ).filter(
        models.FiscalYear.start <= end_date
    ).all()
    return list(map(lambda fy: fy.id, fys))


def fy_to_fyfy(fy):
    """Converts a fiscal year to a year + year+1 e.g. 2018 to 1819"""
    return "{}{}".format(fy[2:4], str(int(fy)+1)[2:4])


def fy_fy_to_fy(fy_fy):
    """Converts a fiscal year FY2019/20 to e.g. 2019"""
    result = re.match(r"FY(\d*)/.*", fy_fy).group(1)
    return int(result)


def fy_fy_to_fyfy_ifmis(fy_fy):
    """Converts a fiscal year FY2019/20 to IFMIS-style 20192020"""
    result1 = re.match(r"FY(\d*)", fy_fy)
    if result1:
        return result1.group(1)
    result2 = re.match(r"FY(\d*)/.*", fy_fy).group(1)
    return "{}{}".format(int(result), int(result)+1)


def column_data_to_string(column_name):
    fq, fy = get_data_from_header(column_name)
    return u"FY{} Q{} Disbursements".format(fy, fq)


def get_real_date_from_header(column_name, start_end="start"):
    fy, fq = get_data_from_header(column_name)
    return (fq_fy_to_date(int(fy), int(fq), start_end=start_end))


def make_quarters_text(list):
    return [{
            "months": range(l["start"][1], l["end"][1]+1),
            "quarter_num": k,
            "quarter_name": "Q{}".format(k),
            "quarter_months": "{}-{}".format(
        datetime.date(2019, l["start"][1], l["start"][0]).strftime("%b"),
        datetime.date(2019, l["end"][1], l["end"][0]).strftime("%b")
    )} for k, l in list.items()]


# The below functions return the FY/FQ according to the format of the
# last fiscal year. E.g. if the last Fiscal Year runs January-December,
# then January (for any year) will be returned as Q1.


def fy_to_fyfy_present(fy):
    """Converts a fiscal year to a year + year+1 e.g. 2018 to 1819,
    but only if the latest fiscal year spans more than one year"""
    fiscal_year = models.FiscalYear.query.order_by(models.FiscalYear.end.desc()).first()
    if fiscal_year.start.year != fiscal_year.end.year:
        return "{}{}".format(fy[2:4], str(int(fy)+1)[2:4])
    return "{}".format(fy[0:4])


def make_quarters_text_present():
    quarters_months = quarters_months_present()
    return make_quarters_text(quarters_months)


def quarters_months_present():
    fiscal_year = models.FiscalYear.query.order_by(models.FiscalYear.end.desc()).first()
    fiscal_periods = fiscal_year.fiscal_year_periods
    return dict(map(lambda period: (period.order, {
        "start": (period.start.day, period.start.month),
        "end": (period.end.day, period.end.month)
    }), fiscal_year.fiscal_year_periods))

def date_to_fy_fq_present(date, quarters_months_text=None):
    if quarters_months_text is None:
        quarters_months_text = make_quarters_text_present()
    months_quarters = dict([(month, quarter['quarter_num'])
        for quarter in quarters_months_text
        for month in quarter['months']])
    list_months_quarters = list(months_quarters)
    quarter = months_quarters[date.month]
    # Q3 and Q4 (Jan-Jun) are FY of previous year
    if list_months_quarters.index(date.month) > list_months_quarters.index(12):
        year = date.year-1
    else:
        year = date.year
    return year, quarter
