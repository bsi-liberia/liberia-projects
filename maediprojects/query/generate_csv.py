# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
import datetime
from maediprojects.query import activity as qactivity
from maediprojects.lib.codelist_helpers import codelists 
from maediprojects.lib.codelists import get_codelists_lookups
import unicodecsv
import StringIO

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
    sum_commitments = {True: sum(map(lambda c: c.transaction_value, activity_commitments)),
          False: activity.total_commitments}[len(activity_commitments) > 0]
    activity_disbursements = filter(valid_transaction, activity.disbursements)
    sum_disbursements = {True: sum(map(lambda d: d.transaction_value, activity_disbursements)),
          False: activity.total_disbursements}[len(activity_disbursements) > 0]
          
    longs = list(map(lambda l: float(l.locations.longitude), activity.locations))
    lats = list(map(lambda l: float(l.locations.latitude), activity.locations))
    
    if len(longs)>0 and len(lats)>0:
        average_longs = sum(longs) / len(longs)
        average_lats = sum(lats) / len(lats)
    else:
        average_longs = ""
        average_lats = ""
    
    return {u'Reporting Organisation': "MAEDI",
     u'Standard activity identifier': { True: activity.code, 
               False: activity.id
             }[bool(activity.code)], 
        u'Other activity identifiers': { True: activity.code, 
               False: activity.id
             }[bool(activity.code)],
        u'Activity Title': activity.title, 
        u"Activity Title (in recipient's language)":"",
        u'Activity Description': activity.description, 
        u"Activity Description (in recipient's language)": "",
        u'Activity Status': cl_lookups["ActivityStatus"][activity.activity_status], 
        u'Activity Dates (Start Date)': activity.start_date.isoformat(),
        u'Activity Dates (End Date)': activity.end_date.isoformat(), 
        u'Activity Contacts': "",
        u'Participating Organisation (Funding)': "France", 
        u'Participating Organisation (Implementing)': activity.implementing_org,
        u'Recipient Country': cl_lookups["Country"][activity.recipient_country_code], 
        u'Recipient Region': "",
        u'Sub-national Geographic Location - Latitude': average_lats, 
        u'Sub-national Geographic Location - Longitude': average_longs,
        u'Sector (DAC CRS)': cl_lookups["Sector"][activity.dac_sector], 
        u'Sector (Agency specific)': cl_lookups["cicid-sectors"][activity.cicid_sector],
        u'Policy Markers': "",
        u'Collaboration Type': cl_lookups["CollaborationType"][activity.collaboration_type], 
        u'Default Flow Type': cl_lookups["FlowType"][activity.flow_type],
        u'Default Finance Type': cl_lookups["FinanceType"][activity.finance_type],
        u'Default Aid Type': cl_lookups["AidType"][activity.aid_type], 
        u'Default Tied Aid Status': cl_lookups["TiedStatus"][activity.tied_status],
        u'Activity Budget': sum_commitments,
        u'Planned Disbursements': "", 
        u'Financial transaction (Commitment)': "", 
        u'Financial transaction (Disbursement & Expenditure)': sum_disbursements, 
        u'Financial transaction (Reimbursement)': "", 
        u'Financial transaction (Incoming Funds)': "", 
        u'Financial transaction (Loan repayment / interest repayment)': "", 
        u'Activity Documents': "", 
        u'Activity Website': "", 
        u'Related Activity': "", 
        u'Conditions attached Y/N': "",
        u'Text of Conditions': "",
        u'Results data': "", 
        u'Cofinancement': u"Non",
        u'Date de mise à jour du projet': activity.updated_date.date().isoformat(), 
        u'Date de la dernière publication': datetime.datetime.now().date().isoformat(),
        u'Date de publication NCO': "", 
        u'CRG': ""}

def generate_csv():
    headers = ['Reporting Organisation', u'Standard activity identifier', 
    u'Other activity identifiers', u'Activity Title', 
    u"Activity Title (in recipient's language)", u'Activity Description', 
    u"Activity Description (in recipient's language)", u'Activity Status', 
    u'Activity Dates (Start Date)', u'Activity Dates (End Date)', 
    u'Activity Contacts', u'Participating Organisation (Funding)', 
    u'Participating Organisation (Implementing)', u'Recipient Country', 
    u'Recipient Region', u'Sub-national Geographic Location - Latitude', 
    u'Sub-national Geographic Location - Longitude', u'Sector (DAC CRS)', 
    u'Sector (Agency specific)', u'Policy Markers', u'Collaboration Type', 
    u'Default Flow Type', u'Default Finance Type', u'Default Aid Type', 
    u'Default Tied Aid Status', u'Activity Budget', u'Planned Disbursements', 
    u'Financial transaction (Commitment)', 
    u'Financial transaction (Disbursement & Expenditure)', 
    u'Financial transaction (Reimbursement)', 
    u'Financial transaction (Incoming Funds)', 
    u'Financial transaction (Loan repayment / interest repayment)', 
    u'Activity Documents', u'Activity Website', u'Related Activity', 
    u'Conditions attached Y/N', u'Text of Conditions', u'Results data', 
    u'Cofinancement', u'Date de mise à jour du projet', 
    u'Date de la dernière publication', u'Date de publication NCO', 
    u'CRG']
    
    fr_headers = ["Société", u"Id. Concours", u"Id. Projet", 
    u"Nom du projet pour les instances", u"Non applicable", 
    u"Description du projet", u"Non applicable", u"Etat du projet", 
    u"Date de 1er versement (projet)", 
    u"Date d’achèvement opérationnel du projet", u"Libellé agence", 
    u"Valeur fixe", u"Libellé bénéficiaire primaire", 
    u"Pays de réalisation", u"Région", u"Latitude", u"Longitude ", 
    u"Libellé secteur économique  (CAD-5)", u"Libellé CICID", 
    u"Non applicable", u"Valeur fixe", u"Libellé indicateur APD", 
    u"Groupe de produit", u"Valeur fixe", u"Valeur fixe", 
    u"Engagements bruts (euro)", u"Non applicable", u"Non applicable", 
    u"Versements (euro)", u"Non applicable", u"Non applicable", 
    u"Non applicable", u"Lien_Fiche_Projet", u"Non applicable", 
    u"Non applicable", u"Non applicable", u"Non applicable", 
    u"Non applicable", u"Cofinanciers (O/N)", 
    u"Date mise à jour données projet", u"Date de la dernière publication", 
    u"Date de publication NCO", u"CRG"]
    
    csv_file = StringIO.StringIO()
    cl_lookups = get_codelists_lookups()
    
    csv = unicodecsv.DictWriter(csv_file, headers)
    csv.writeheader()
    fr_headers_row = dict(map(lambda x: (x[1], fr_headers[x[0]]), enumerate(headers)))
    csv.writerow(fr_headers_row)
    
    activities = qactivity.list_activities()
    for activity in activities:
        csv.writerow(activity_to_json(activity, cl_lookups))
    return csv_file
