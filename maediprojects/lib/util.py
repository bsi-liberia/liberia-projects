import datetime
import re
import collections

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
    3: {"start": (1, 1), "end": (31, 3)},
    4: {"start": (1, 4), "end": (30, 6)},
    1: {"start": (1, 7), "end": (30, 9)},
    2: {"start": (1, 10), "end": (31, 12)}
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
    if _fq in (3,4):
        year = _fy+1
    else:
        year = _fy
    quarter = LR_QUARTERS_CAL_QUARTERS[_fq]
    return year, quarter

def fp_fy_to_date(fp, fy, start_end='start'):
    """Convert from LR FP, FY to real date."""
    if fp in ("M7","M8","M9","M10","M11","M12","M13"):
        year = fy+1
    else:
        year = fy
    day, month = LR_PERIODS_MONTH_DAY[fp][start_end]
    return datetime.datetime(year, month, day)

def fq_fy_to_date(fq, fy, start_end='start'):
    """Convert from LR FQ, FY to real date."""
    if fq in (3,4):
        year = fy+1
    else:
        year = fy
    day, month = LR_QUARTERS_MONTH_DAY[fq][start_end]
    return datetime.datetime(year, month, day)

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
    if value == "": return None
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

def available_fys():
    return ["FY{}/{}".format(str(year), str(year+1)[2:]) for year in ALLOWED_YEARS]

def available_fy_fqs():
    return ["{} Q{} (D)".format(year, quarter) for year in ALLOWED_YEARS for quarter in (1,2,3,4)]

def current_fy_fq():
    year, quarter = date_to_fy_fq(datetime.datetime.utcnow())
    return "{} Q{} (D)".format(year, quarter)

def previous_fy_fq():
    year, quarter = date_to_fy_fq(datetime.datetime.utcnow())
    year, quarter = subtract_one_quarter(year, quarter)
    return "{} Q{} (D)".format(year, quarter)

def previous_fy_fq_numeric():
    year, quarter = date_to_fy_fq(datetime.datetime.utcnow())
    return subtract_one_quarter(year, quarter)

def previous_fy_fq_date(start_end="end"):
    year, quarter = previous_fy_fq_numeric()
    return fq_fy_to_date(quarter, year, start_end)

class Last4Quarters:
    def start(self):
        """The start of the quarter one year ago."""
        year, quarter = date_to_fy_fq(self.FY.current_date - datetime.timedelta(days=365))
        return fq_fy_to_date(quarter, year, start_end="start")

    def end(self):
        """End of the previous quarter from today: because we don't want to include
        the current incomplete quarter"""
        year, quarter = subtract_one_quarter(*date_to_fy_fq(self.FY.current_date))
        return fq_fy_to_date(quarter, year, start_end="end")

    def list_of_quarters(self):
        start = self.start()
        year, quarter = date_to_fy_fq(start)
        out = collections.OrderedDict({})
        for i in range(4):
            out["Q{}".format(quarter)] = "FY{} Q{}".format(year, quarter)
            year, quarter = add_one_quarter(year, quarter)
        return out

    def __init__(self):
        self.FY = FY("current")

class FY:
    def fy_to_date(self, fy, start_end):
        return fq_fy_to_date({"start": 1, "end": 4}[start_end], fy, start_end)

    def fy_fy(self):
        year, quarter = self.numeric()
        year_q1 = self.fy_to_date(year, "start").year
        year_q4 = self.fy_to_date(year, "end").year
        return "FY{}/{}".format(year_q1, str(year_q4)[2:])

    def fy(self):
        year, quarter = date_to_fy_fq(datetime.datetime.utcnow())
        return "{}".format(year)

    def numeric(self):
        year, quarter = date_to_fy_fq(self.current_date)
        return year, quarter

    def date(self, start_end="end"):
        fy, fq = self.numeric()
        return self.fy_to_date(fy, start_end)

    def __init__(self, current_previous):
        if current_previous == "current":
            self.current_date = datetime.datetime.utcnow()
        elif current_previous == "previous":
            self.current_date = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        elif current_previous == "next":
            self.current_date = datetime.datetime.utcnow() + datetime.timedelta(days=365)
        else:
            raise Exception


def available_fy_fqs_as_dict():
    return [{'value': fyfqstring,
             'text': column_data_to_string(fyfqstring),
             'selected': previous_fy_fq() == fyfqstring
              } for fyfqstring in available_fy_fqs()]

def get_data_from_header(column_name):
    pattern = r"(\d*) Q(\d) \(D\)"
    result = re.match(pattern, column_name).groups()
    return (result[1], result[0])

def fy_to_fyfy(fy):
    """Converts a fiscal year to a year + year+1 e.g. 2018 to 1819"""
    return "{}{}".format(fy[2:4], str(int(fy)+1)[2:4])

def fy_fy_to_fy(fy_fy):
    """Converts a fiscal year FY2019/20 to e.g. 2019"""
    result = re.match(r"FY(\d*)/.*", fy_fy).group(1)
    return int(result)

def fy_fy_to_fyfy_ifmis(fy_fy):
    """Converts a fiscal year FY2019/20 to IFMIS-style 20192020"""
    result = re.match(r"FY(\d*)/.*", fy_fy).group(1)
    return "{}{}".format(int(result), int(result)+1)

def column_data_to_string(column_name):
    fq, fy = get_data_from_header(column_name)
    fyfy = fy_to_fyfy(fy)
    return u"FY{} Q{} Disbursements".format(fyfy, fq)

def get_real_date_from_header(column_name, start_end="start"):
    fy, fq = get_data_from_header(column_name)
    return (fq_fy_to_date(int(fy), int(fq), start_end=start_end))

def make_quarters_text(list):
    return [{"quarter_name": "Q{}".format(k),
        "quarter_months": "{}-{}".format(
        datetime.date(2019, l["start"][1], l["start"][0]).strftime("%b"),
        datetime.date(2019, l["end"][1], l["end"][0]).strftime("%b")
    )} for k, l in list.items()]
