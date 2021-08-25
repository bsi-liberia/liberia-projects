# -*- coding: UTF-8 -*-

import datetime
import sys
if sys.version_info.major == 2:
    import unicodecsv
else:
    import csv as unicodecsv
import io
import re

from projectdashboard.query import activity as qactivity
from projectdashboard.lib import util
from projectdashboard.lib.codelists import get_codelists_lookups
from projectdashboard.lib.spreadsheet_headers import headers
from projectdashboard import models


def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")


def date_isostring(value):
    # Returns a string of format YYYY-MM-DD from a date object
    return value.isoformat()


def current_datetime():
    return datetime.datetime.now().replace(
        microsecond=0).isoformat()


def actual_or_planned(value):
    date = isostring_date(value)
    current_datetime = datetime.datetime.now()
    if date > current_datetime:
        return "actual"
    return "planned"


def valid_transaction(transaction):
    return (transaction.transaction_date and transaction.transaction_value > 0)


def activity_to_json(activity, cl_lookups):
    activity_commitments = filter(valid_transaction, activity.commitments)
    sum_commitments = sum(
        map(lambda c: c.transaction_value, activity_commitments))

    activity_disbursements = filter(valid_transaction, activity.disbursements)
    sum_disbursements = sum(
        map(lambda d: d.transaction_value, activity_disbursements))

    def get_code_or_blank(activity, codelist):
        if codelist in activity.classification_data:
            return ",".join(list(map(lambda x: x.codelist_code.name, activity.classification_data[codelist]["entries"])))
        return ""

    data = {u'Reported by': activity.reporting_org.name,
            u'ID': activity.id,
            u'Project code': activity.code,
            u'Domestic/External': activity.domestic_external,
            u'Activity Title': re.sub("\t|\n|\r", "", activity.title if activity.title is not None else ''),
            u'Activity Description': re.sub("\t|\n|\r", "", activity.description if activity.description is not None else ''),
            u'Activity Status': cl_lookups["ActivityStatus"].get(activity.activity_status),
            u'Activity Dates (Start Date)': activity.start_date.isoformat() if activity.start_date else "",
            u'Activity Dates (End Date)': activity.end_date.isoformat() if activity.end_date else "",
            u'County': ", ".join(list(map(lambda l: l.locations.name, activity.locations))),
            u'Funded by': ",".join(list(map(lambda x: x.name, activity.funding_organisations))),
            u'Implemented by': ",".join(list(map(lambda x: x.name, activity.implementing_organisations))),
            u'Sector (DAC CRS)': cl_lookups["Sector"].get(activity.dac_sector, ""),
            u'MTEF Sector': get_code_or_blank(activity, "mtef-sector"),
            u'Aligned Ministry/Agency': get_code_or_blank(activity, "aligned-ministry-agency"),
            u'PAPD Pillar': get_code_or_blank(activity, "papd-pillar"),
            u'AfT Pillar': get_code_or_blank(activity, "aft-pillar"),
            u'Collaboration Type (Donor Type)': cl_lookups["CollaborationType"].get(activity.collaboration_type),
            u'Finance Type (Type of Assistance)': cl_lookups["FinanceType"].get(activity.finance_type),
            u'Aid Type (Aid Modality)': cl_lookups["AidType"].get(activity.aid_type),
            u'Activity Budget': "",
            u'Planned Disbursements': "",
            u'Total Commitments': sum_commitments,
            u'Total Disbursements': sum_disbursements,
            u'Activity Documents': "",
            u'Activity Website': "",
            u'Last updated date': activity.updated_date.date().isoformat(),
            }
    # Add Disbursements data
    data.update(dict(
        map(lambda d: (d[0], d[1]["value"]), activity.FY_disbursements_dict.items())))
    # Add MTEF data
    data.update(dict(
        map(lambda d: (d[0], d[1]["value"]), activity.FY_forward_spend_dict.items())))

    data.update(dict(map(lambda d: (d, 0.00), list(
        filter(lambda h: h not in data, generate_disb_fys())))))
    return data


def disb_fy_fqs():
    available_fys = util.available_fys()
    fps = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.fiscal_year_id.in_(available_fys)
    ).order_by(models.FiscalPeriod.start).all()
    return [("{} {} (D)".format(fp.fiscal_year_id, fp.name)
             ) for fp in fps]


def disb_fy_fqs_with_mtefs():
    available_fys = util.available_fys()
    fps = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.fiscal_year_id.in_(available_fys)
    ).order_by(models.FiscalPeriod.start).all()
    MTEF_QTRS = [("{} {} (MTEF)".format(fp.fiscal_year_id, fp.name)
                  ) for fp in fps]
    DISB_QTRS = [("{} {} (D)".format(fp.fiscal_year_id, fp.name)
                  ) for fp in fps]
    return MTEF_QTRS + DISB_QTRS


def mtef_fy_fqs(start=datetime.datetime.utcnow().year+1, end=False):
    available_fys = util.available_fys()
    fps = models.FiscalPeriod.query.filter(
        models.FiscalPeriod.fiscal_year_id.in_(available_fys)
    ).order_by(models.FiscalPeriod.start).all()
    MTEF_QTRS = [("{} {} (MTEF)".format(fp.fiscal_year_id, fp.name)
                  ) for fp in fps]
    return MTEF_QTRS


def mtef_fys(num_years=3, forward=False):
    if forward:
        mtef_fys = util.available_fys_forward()
    else:
        mtef_fys = util.available_fys()
    return ["{} (MTEF)".format(mtef_fy) for mtef_fy in mtef_fys]


def counterpart_fys(num_years=1, forward=False):
    if forward:
        counterpart_fys = util.available_fys_forward(num_years)
    else:
        counterpart_fys = util.available_fys(num_years)
    return ["{} (GoL counterpart fund request)".format(counterpart_fy) for counterpart_fy in counterpart_fys]


def generate_disb_fys():
    return disb_fy_fqs_with_mtefs()


def generate_csv():
    csv_file = io.StringIO()
    cl_lookups = get_codelists_lookups()
    disb_fys = generate_disb_fys()
    _headers = headers + disb_fys
    csv = unicodecsv.DictWriter(csv_file, _headers)
    csv.writeheader()
    activities = qactivity.list_activities()
    for activity in activities:
        activity_data = activity_to_json(activity, cl_lookups)
        remove_keys = set(activity_data)-set(_headers)
        for remove_key in remove_keys:
            del activity_data[remove_key]
        csv.writerow(activity_data)
    return csv_file


def activity_to_transactions_list(activity, cl_lookups):

    def get_code_or_blank(activity, codelist):
        if codelist in activity.classification_data:
            return ",".join(list(map(lambda x: x.codelist_code.name, activity.classification_data[codelist]["entries"])))
        return ""

    def make_transaction(activity, tr, transaction_type, fiscal_periods):
        return {u'Reported by': activity.reporting_org.name,
                u'ID': activity.id,
                u'Project code': activity.code,
                u'Domestic/External': activity.domestic_external,
                u'Activity Title': re.sub("\t|\n|\r", "", activity.title if activity.title is not None else ''),
                u'Activity Description': re.sub("\t|\n|\r", "", activity.description if activity.description is not None else ''),
                u'Activity Status': cl_lookups["ActivityStatus"].get(activity.activity_status),
                u'Activity Dates (Start Date)': activity.start_date.isoformat() if activity.start_date else "",
                u'Activity Dates (End Date)': activity.end_date.isoformat() if activity.end_date else "",
                u'County': ", ".join(list(map(lambda l: l.locations.name, activity.locations))),
                u'Funded by': ",".join(list(map(lambda x: x.name, activity.funding_organisations))),
                u'Implemented by': ",".join(list(map(lambda x: x.name, activity.implementing_organisations))),
                u'Sector (DAC CRS)': cl_lookups["Sector"].get(activity.dac_sector, ""),
                u'MTEF Sector': get_code_or_blank(activity, "mtef-sector"),
                u'Aligned Ministry/Agency': get_code_or_blank(activity, "aligned-ministry-agency"),
                u'PAPD Pillar': get_code_or_blank(activity, "papd-pillar"),
                u'AfT Pillar': get_code_or_blank(activity, "aft-pillar"),
                u'Collaboration Type (Donor Type)': cl_lookups["CollaborationType"].get(activity.collaboration_type),
                u'Finance Type (Type of Assistance)': cl_lookups["FinanceType"].get(activity.finance_type),
                u'Aid Type (Aid Modality)': cl_lookups["AidType"].get(activity.aid_type),
                u'Last updated date': activity.updated_date.date().isoformat(),
                u"Fiscal Year": tr["fiscal_year"],
                u"Fiscal Quarter": tr["fiscal_quarter"],
                u"Transaction Date": fiscal_periods.get((tr["fiscal_year"], tr["fiscal_quarter"])).isoformat(),
                u"Transaction Value": tr["value"],
                u"Transaction Type": transaction_type
                }

    db_fiscal_periods = models.FiscalPeriod.query.all()
    fiscal_periods = dict(
        map(lambda fp: ((fp.fiscal_year_id, fp.name), fp.start), db_fiscal_periods))

    transactions = []
    for tr in activity.FY_commitments_dict.values():
        transactions.append(make_transaction(
            activity, tr, u"Commitment", fiscal_periods))
    for tr in activity.FY_disbursements_dict.values():
        transactions.append(make_transaction(
            activity, tr, u"Disbursement", fiscal_periods))
    for tr in activity.FY_forward_spend_dict.values():
        transactions.append(make_transaction(
            activity, tr, u"MTEF Projection", fiscal_periods))
    return transactions
