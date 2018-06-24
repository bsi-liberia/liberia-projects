# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
import datetime
from maediprojects.query import activity as qactivity
from maediprojects.lib.codelist_helpers import codelists 
from maediprojects.lib.codelists import get_codelists_lookups
from maediprojects.lib.spreadsheet_headers import headers, fr_headers
import unicodecsv
import StringIO
import re

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
          
    longs = list(map(lambda l: float(l.locations.longitude), activity.locations))
    lats = list(map(lambda l: float(l.locations.latitude), activity.locations))
    
    if len(longs)>0 and len(lats)>0:
        average_longs = sum(longs) / len(longs)
        average_lats = sum(lats) / len(lats)
    else:
        average_longs = ""
        average_lats = ""
    
    return {u'Reporting Organisation': "MFDP",
     u'Project code': { True: activity.code, 
               False: activity.id
             }[bool(activity.code)],
        u'Activity Title': re.sub("\t|\n|\r", "", activity.title), 
        u"Activity Title (in recipient's language)":"",
        u'Activity Description': re.sub("\t|\n|\r", "", activity.description), 
        u"Activity Description (in recipient's language)": "",
        u'Activity Status': cl_lookups["ActivityStatus"][activity.activity_status], 
        u'Activity Dates (Start Date)': activity.start_date.isoformat() if activity.start_date else "",
        u'Activity Dates (End Date)': activity.end_date.isoformat() if activity.end_date else "", 
        u'Activity Contacts': "",
        u'Participating Organisation (Funding)': activity.funding_org.name, 
        u'Participating Organisation (Implementing)': activity.implementing_org,
        u'Recipient Country': cl_lookups["Country"][activity.recipient_country_code], 
        u'Recipient Region': "",
        u'Sub-national Geographic Location - Latitude': average_lats, 
        u'Sub-national Geographic Location - Longitude': average_longs,
        u'Sector (DAC CRS)': cl_lookups["Sector"].get(activity.dac_sector, ""), 
        u'Sector (Agency specific)': activity.classification_data["mtef-sector"].codelist_code.name,
        u'Policy Markers': "",
        u'Collaboration Type': cl_lookups["CollaborationType"][activity.collaboration_type], 
        u'Default Flow Type': cl_lookups["FlowType"][activity.flow_type],
        u'Default Finance Type': cl_lookups["FinanceType"][activity.finance_type],
        u'Default Aid Type': cl_lookups["AidType"][activity.aid_type], 
        u'Default Tied Aid Status': cl_lookups["TiedStatus"][activity.tied_status],
        u'Activity Budget': "",
        u'Planned Disbursements': "", 
        u'Financial transaction (Commitment)': sum_commitments, 
        u'Financial transaction (Disbursement & Expenditure)': sum_disbursements, 
        u'Financial transaction (Reimbursement)': "", 
        u'Financial transaction (Incoming Funds)': "", 
        u'Financial transaction (Loan repayment / interest repayment)': "", 
        u'Activity Documents': "", 
        u'Activity Website': "", 
        u'Last updated date': activity.updated_date.date().isoformat()
    }

def generate_csv():
    csv_file = StringIO.StringIO()
    cl_lookups = get_codelists_lookups()
    
    csv = unicodecsv.DictWriter(csv_file, headers)
    csv.writeheader()
    
    activities = qactivity.list_activities()
    for activity in activities:
        csv.writerow(activity_to_json(activity, cl_lookups))
    return csv_file
