# -*- coding: UTF-8 -*-

import datetime
import unicodecsv
from io import StringIO
import re

from maediprojects.query import activity as qactivity
from maediprojects.lib import util
from maediprojects.lib.codelists import get_codelists_lookups
from maediprojects.lib.spreadsheet_headers import headers


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
    sum_commitments = sum(map(lambda c: c.transaction_value, activity_commitments))

    activity_disbursements = filter(valid_transaction, activity.disbursements)
    sum_disbursements = sum(map(lambda d: d.transaction_value, activity_disbursements))

    def get_code_or_blank(activity, codelist):
        if codelist in activity.classification_data:
            return ",".join(list(map(lambda x: x.codelist_code.name, activity.classification_data[codelist]["entries"])))
        return ""

    data = {u'Reported by': activity.reporting_org.name,
        u'ID': activity.id,
        u'Project code': activity.code,
        u'Domestic/External': activity.domestic_external,
        u'Activity Title': re.sub("\t|\n|\r", "", activity.title),
        u'Activity Description': re.sub("\t|\n|\r", "", activity.description),
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
    data.update(dict(map(lambda d: (d[0], d[1]["value"]), activity.FY_disbursements_dict.items())))
    # Add MTEF data
    data.update(dict(map(lambda d: (d[0], d[1]["value"]), activity.FY_forward_spend_dict.items())))

    data.update(dict(map(lambda d: (d, 0.00), list(filter(lambda h: h not in data, generate_disb_fys())))))
    return data


def disb_fy_fqs(start=2013):
    disbFYs_QTRs = [("{} Q1 (D)".format(fy), "{} Q2 (D)".format(fy),
             "{} Q3 (D)".format(fy), "{} Q4 (D)".format(fy)
             ) for fy in range(2013, datetime.datetime.utcnow().year+1)]
    return [item for sublist in disbFYs_QTRs for item in sublist]


def disb_fy_fqs_with_mtefs(start=2013):
    disbFYs_QTRs = [("{} Q1 (MTEF)".format(fy), "{} Q2 (MTEF)".format(fy),
                     "{} Q3 (MTEF)".format(fy), "{} Q4 (MTEF)".format(fy),
                     "{} Q1 (D)".format(fy), "{} Q2 (D)".format(fy),
                     "{} Q3 (D)".format(fy), "{} Q4 (D)".format(fy)
             ) for fy in range(2013, datetime.datetime.utcnow().year+1)]
    return [item for sublist in disbFYs_QTRs for item in sublist]


def mtef_fy_fqs(start=datetime.datetime.utcnow().year+1, end=False):
    MTEFFYs_QTRs = [("{} Q1 (MTEF)".format(fy), "{} Q2 (MTEF)".format(fy),
                     "{} Q3 (MTEF)".format(fy), "{} Q4 (MTEF)".format(fy)
                     ) for fy in range(start, {False: start+3, True: end}[bool(end)])]
    return [item for sublist in MTEFFYs_QTRs for item in sublist]


def mtef_fys(start=datetime.datetime.utcnow().date().year,
        end=datetime.datetime.utcnow().date().year+3):
    return [u"FY{}/{} (MTEF)".format(str(year)[2:4], str(year+1)[2:4]) for year in range(start, end)]


def counterpart_fys(start=datetime.datetime.utcnow().date().year,
        end=datetime.datetime.utcnow().date().year+1):
    return [u"FY{}/{} (GoL counterpart fund request)".format(str(year)[2:4], str(year+1)[2:4]) for year in range(start, end)]


def generate_disb_fys():
    #FIXME don't hard code start year
    disbFYs_QTRs = disb_fy_fqs_with_mtefs()
    MTEFFYs_QTRs = mtef_fy_fqs()
    return disbFYs_QTRs+MTEFFYs_QTRs

def generate_csv():
    csv_file = StringIO.StringIO()
    cl_lookups = get_codelists_lookups()
    disb_fys = generate_disb_fys()
    _headers = headers + disb_fys
    csv = unicodecsv.DictWriter(csv_file, _headers)
    csv.writeheader()
    activities = qactivity.list_activities()
    for activity in activities:
        activity_data = activity_to_json(activity, cl_lookups)
        remove_keys = set(activity_data)-set(_headers)
        for remove_key in remove_keys: del activity_data[remove_key]
        csv.writerow(activity_data)
    return csv_file

def activity_to_transactions_list(activity, cl_lookups):

    def get_code_or_blank(activity, codelist):
        if codelist in activity.classification_data:
            return ",".join(list(map(lambda x: x.codelist_code.name, activity.classification_data[codelist]["entries"])))
        return ""

    def make_transaction(activity, tr, transaction_type):
        return {u'Reported by': activity.reporting_org.name,
            u'ID': activity.id,
            u'Project code': activity.code,
            u'Domestic/External': activity.domestic_external,
            u'Activity Title': re.sub("\t|\n|\r", "", activity.title),
            u'Activity Description': re.sub("\t|\n|\r", "", activity.description),
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
            u"Transaction Date": util.fq_fy_to_date(int(tr["fiscal_quarter"][1]),
                int(tr["fiscal_year"]), start_end='start').date().isoformat(),
            u"Transaction Value": tr["value"],
            u"Transaction Type": transaction_type
        }

    transactions = []
    for tr in activity.FY_commitments_dict.values():
        transactions.append(make_transaction(activity, tr, u"Commitment"))
    for tr in activity.FY_disbursements_dict.values():
        transactions.append(make_transaction(activity, tr, u"Disbursement"))
    for tr in activity.FY_forward_spend_dict.values():
        transactions.append(make_transaction(activity, tr, u"MTEF Projection"))
    return transactions
