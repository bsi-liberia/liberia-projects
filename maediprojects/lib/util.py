import datetime

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
