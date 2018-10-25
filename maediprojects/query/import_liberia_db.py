# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
from maediprojects.lib import codelists, xlsx_to_csv, util
from maediprojects.query import user as quser
from maediprojects.query import activity as qactivity
from maediprojects.query import codelists as qcodelists
from maediprojects.query import location as qlocations
from maediprojects.query import finances as qfinances
from maediprojects.query import organisations as qorganisations
import normality
import os, re
import datetime as dt
basedir = os.path.abspath(os.path.dirname(__file__))

def read_file(FILENAME=os.path.join(basedir, "..", "lib/import_files/", "AMCU_Master_Database.xlsx")):
    f = open(FILENAME, "rb")
    return xlsx_to_csv.getDataFromFile(f, f.read(), sheet="Main Database June 2017")

def nonempty_from_list(some_list):
    for item in some_list:
        if item.strip() != "": return item 
    return ""

def get_date(date_value):
    date_value = date_value.strip()
    if re.match("^\d{5}$", date_value): # Excel date like 43465
        temp = dt.datetime(1899, 12, 30)
        delta = dt.timedelta(days=int(date_value))
        return (temp+delta).date()
    if re.match("^\d{2}/\d{2}/\d{4}$", date_value): # dd/mm/yyyy
        return dt.datetime.strptime(date_value, "%d/%m/%Y").date()
    if date_value == "":
        return dt.datetime.utcnow().date()
    raise Exception ## Warn of strangely formatted dates
    
CODES = {
    "collaboration_type": {
        "Multilateral": u"4",
        "Bilateral": u"1",
        "": u"1"
    },
    "finance_type": {
        "Loan": u"410",
        "Grant": u"110",
        "": u"110"
    },
    "aid_type": {
        "Trust Fund": u"B03",
        "Budget Support": u"A01",
        "Project/Program Aid": u"C01",
        "Pool Fund": u"B04",
        "": u"C01"
    },
    "activity_status": {
        "Cancelled": u"5",
        "Executing": u"2",
        "On-going": u"2",
        "Ratified": u"91",
        "Signed": u"92",
        "signed": u"92",
        "Started": u"2",
        "": u"2"
    }
}

def tidy_amount(amount_value):
    amount_value = amount_value.strip()
    amount_value = re.sub(",", "", amount_value)
    if re.match("^\d*$", amount_value): # 2000
        return (float(amount_value), u"USD")
    elif re.match('(\d*\.\d*)', amount_value):
        return (float(amount_value), u"USD")
    elif re.match("^(\d*)m (\D*)$", amount_value): # 20m EUR
        result = re.match("^(\d*)m (\D*)$", amount_value).groups()
        return (float(result[0])*1000000, unicode(result[1].upper()))
    elif re.match("^(\d*) (\D*)$", amount_value): # 2000 EUR
        result = re.match("^(\d*) (\D*)$", amount_value).groups()
        return (float(result[0]), unicode(result[1].upper()))

def process_transactions(activity, start_date, CODELISTS_IDS_BY_NAME):
    provider = clean_get_create_organisation(activity["Funding agency"])
    receiver = clean_get_create_organisation(activity["Implementing Agency"])
    
    transactions = []
    commitment_cols = ["Cost"]
    for col in commitment_cols:
        if activity[col].strip() in ("", "-", "0"): continue
        amount, currency = tidy_amount(activity[col])
        commitment = models.ActivityFinances()
        commitment.transaction_date = start_date
        commitment.transaction_type = u"C"
        commitment.transaction_description = u"Cost, imported from AMCU data"
        commitment.transaction_value = float(amount)
        commitment.currency = currency
        commitment.provider_org_id = provider
        commitment.receiver_org_id = receiver
        commitment.finance_type = CODES["finance_type"][
            activity["Type Of Assistance"].strip()
        ]
        commitment.aid_type = CODES["aid_type"][
            activity["Aid Modality"].strip()
        ]
        commitment.classifications = process_transaction_classifications(activity, CODELISTS_IDS_BY_NAME)
        transactions.append(commitment)
    disbursement_cols = ['Actual Disbursements Q1 FY13/14', 
    'Actual Disbursements Q2 FY13/14', 'Actual Disbursements Q3 FY13/14', 
    'Actual Disbursements Q4 FY13/14', 'Actual Disbursement Q1 FY14/15', 
    'Actual Disbursement Q2 FY14/15', 'Actual Disbursement Q3 FY14/15', 
    'Actual Disbursement Q4 FY14/15', 'Actual Disbursement Q1 FY15/16', 
    'Actual Disbursement Q2 FY15/16', 'Actual Disbursement Q3 FY15/16', 
    'Actual Disbursement Q4 FY15/16', 'Actual Disbursement Q1 FY16/17', 
    'Actual Disbursement Q2 FY16/17', 'Actual Disbursement Q3 FY16/17', 
    'Actual Disbursement Q4 FY16/17', 'Actual Disbursement Q 1', 
    'Actual Disbursement Q 2', 'Actual Disbursement Q 3']

    def get_data_from_header(column_name):
        patterns = ["Actual Disbursements Q(\d) FY(\d*)/\d*",
            "Actual Disbursement Q(\d) FY(\d*)/\d*",
            "Actual Disbursement Q (\d)"
        ]
        for pattern in patterns:
            if re.match(pattern, column_name):
                result = re.match(pattern, column_name).groups()
                if len(result) == 1:
                    return (result[0], "17")
                return (result[0], result[1])
        raise Exception

    def get_fy_fq_date(fq, fy):
        qtrs = {"1": "09-30",
                "2": "12-31",
                "3": "03-31",
                "4": "06-30"}
        if fq in ("3","4"):
            fy = int(fy)+1
        return "20{}-{}".format(fy,qtrs[fq])

    for col in disbursement_cols:
        col_name = col.strip()
        fq, fy = get_data_from_header(col)
        end_fq_date = get_fy_fq_date(fq, fy)
        
        if activity[col].strip() in ("", "-", "0"): continue
        amount, currency = tidy_amount(activity[col])
        disbursement = models.ActivityFinances()
        disbursement.transaction_date = dt.datetime.strptime(end_fq_date, 
            "%Y-%m-%d")
        disbursement.transaction_type = u"D"
        disbursement.transaction_description = u"Disbursement for Q{} FY{}, imported from AMCU data".format(
            fq, fy
        )
        disbursement.transaction_value = float(amount)
        disbursement.currency = currency
        disbursement.provider_org_id = provider
        disbursement.receiver_org_id = receiver
        disbursement.finance_type = CODES["finance_type"][
            activity["Type Of Assistance"].strip()
        ]
        disbursement.aid_type = CODES["aid_type"][
            activity["Aid Modality"].strip()
        ]
        disbursement.classifications = process_transaction_classifications(activity, CODELISTS_IDS_BY_NAME)
        transactions.append(disbursement)
    return transactions

def process_forward_spends(activity, start_date, end_date):
    forwardspends = []
    """Take earliest of start_date or first forward spend date.
    From then until latest of end_date or last forward spend date, add
    either a value or 0.
    Return list of forward spends, start_date and end_date."""
    mtef_cols = ['MTEF 2013/2014', 'MTEF 2014/2015', 'MTEF 2015/2016', 
    'MTEF 2016/2017', 'MTEF 2017/2018', 'MTEF 2018/2019', 'MTEF 2019/2020']
    
    def get_activity_mtefs(activity):
        activity_mtefs = {}
        for col in mtef_cols:
            if activity[col].strip() in ("", "-", "0"): continue
            mtef_year = int(re.match("MTEF (\d{4})/\d{4}", col).groups()[0])
            activity_mtefs[mtef_year] = tidy_amount(activity[col])[0]
        return activity_mtefs
    
    activity_mtefs = get_activity_mtefs(activity)
    # If there is no MTEF data, set everything to 0
    if len(activity_mtefs) == 0:
        forwardspends = (
            qfinances.create_forward_spends(
                start_date, 
                end_date
            )
        )
        return start_date, end_date, forwardspends
    
    first_mtef = min(activity_mtefs)
    last_mtef = max(activity_mtefs)
    
    start_date_fy, start_date_fq = util.date_to_fy_fq(start_date)
    end_date_fy, end_date_fq = util.date_to_fy_fq(end_date)
    if start_date_fy < first_mtef:
        forwardspends += (
            qfinances.create_forward_spends(
                start_date, 
                util.fq_fy_to_date(1, first_mtef, 'start')-dt.timedelta(days=1)
            )
        )
    
    for mtef_year, mtef_value in activity_mtefs.items():
        forwardspends += (
            qfinances.create_forward_spends(
                util.fq_fy_to_date(1, mtef_year, 'start'),
                util.fq_fy_to_date(4, mtef_year, 'end'),
                mtef_value
            )
        )
    
    # create 0-value quarters up to first mtef
    if end_date_fy > last_mtef:
        forwardspends += (
            qfinances.create_forward_spends(
                dt.datetime(last_mtef+1, 1, 1),
                end_date
            )
        )
    
    #FIXME decide whether to do this…
    # Make adjustments to start/end dates if there are MTEFs found
    #  outside of these dates
    #if first_mtef < start_date.fy:
    #    first = util.fq_fy_to_date(1, first_mtef, "start")
    #if last_mtef > end_date_fy:
    #    end_date = util.fq_fy_to_date(4, last_mtef, "end")
    
    return start_date, end_date, forwardspends

def get_locations_as_lookup():
    locations = qlocations.get_locations_country("LR")
    def filter_ADM1(location):
        return location.feature_code == u'ADM1'
    return dict(map(lambda l: (l.name.replace(" County", "").lower(), l.id),
        filter(filter_ADM1, locations)))

def process_locations(activity, LOCATIONS):
    activity_locations = []
    
    counties_string = activity["County"].lower()
    for location_name, location_id in LOCATIONS.items():
        if location_name in counties_string:
            l = models.ActivityLocation()
            l.location_id = location_id
            activity_locations.append(l)
    return activity_locations

def process_transaction_classifications(activity, CODELISTS_IDS_BY_NAME):
    classifications = []
    cl = models.ActivityFinancesCodelistCode()
    cl.codelist_id = 'mtef-sector'
    cl.codelist_code_id = CODELISTS_IDS_BY_NAME["mtef-sector"][activity["Secondary Sector"].strip()]
    classifications.append(cl)
    return classifications

def process_classifications(activity, CODELISTS_IDS_BY_NAME):
    
    classifications = []
    cl = models.ActivityCodelistCode()
    cl.codelist_code_id = CODELISTS_IDS_BY_NAME["mtef-sector"][activity["Secondary Sector"].strip()]
    classifications.append(cl)

    cl = models.ActivityCodelistCode()
    cl.codelist_code_id = CODELISTS_IDS_BY_NAME["aligned-ministry-agency"][activity["Aligned Ministry Agency"].strip()]
    classifications.append(cl)

    AFT_PILLARS = {
        "Peace, Security and Rule of Law - 1": "Peace, Security and Rule of Law",
        "Economic Transformation": "Economic Transformation",
        "Economic Transformation- 2": "Economic Transformation",
        "Human Development- 3": "Human Development",
        "Governance and Public Institutions - 4": "Governance and Public Institutions",
        "Cross - cutting - 5": "Cross-cutting",
        "Cross-cutting - 5": "Cross-cutting"
    }
    cl = models.ActivityCodelistCode()
    cl.codelist_code_id = CODELISTS_IDS_BY_NAME["aft-pillar"][AFT_PILLARS[activity["Agenda For Transformation Pillar"].strip()]]
    classifications.append(cl)

    cl = models.ActivityCodelistCode()
    cl.codelist_code_id = CODELISTS_IDS_BY_NAME["sdg-goals"][""]
    classifications.append(cl)
    return classifications

def clean_get_create_organisation(_name):
    name = unicode(_name.decode("utf-8")).strip()
    return qorganisations.get_or_create_organisation(name)

def make_organisation(name, role):
    organisation_id = clean_get_create_organisation(name)
    activity_org = models.ActivityOrganisation()
    activity_org.organisation_id = organisation_id
    activity_org.role = role
    return activity_org

def import_file():
    qlocations.import_locations("LR")
    data = read_file()
    print("There are {} projects found".format(len(data)))
    
    # Get location data and codelists for lookup
    LOCATIONS = get_locations_as_lookup()
    CODELISTS_BY_NAME = codelists.get_codelists_lookups_by_name()
    CODELISTS_IDS_BY_NAME = codelists.get_codelists_ids_by_name()
    
    for activity in data:
        start_date = get_date(nonempty_from_list([
                activity["Ratification Date"],
                activity["Ratification date"],
                activity["Signed Start Date"],
                activity["Signing date"]
            ]))
        end_date = get_date(nonempty_from_list([
                        activity["Completion Signed Date"],
                    ]))
        # We adjust start_date and end_date if there are forward spends
        #FIXME: this is switched off currently
        start_date, end_date, forwardspends = process_forward_spends(
            activity, start_date, end_date
        )
        
        d = {
            "user_id": 1, #FIXME
            "domestic_external": u"external",
            "code": "", #FIXME
            "title": unicode(activity["Project Name"].decode("utf-8")),
            "description": nonempty_from_list([
                unicode(activity["Project Description"].decode("utf-8")),
                unicode(activity["Objective"].decode("utf-8")),
            ]),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reporting_org_id": qorganisations.get_or_create_organisation(
                unicode(activity["Funding agency"].decode("utf-8").strip())),
            "organisations": [
                make_organisation(activity["Implementing Agency"], 4),
                make_organisation(activity["Funding agency"], 1)
            ],
            "implementing_org": unicode(activity["Implementing Agency"].decode("utf-8")),
            "recipient_country_code": "LR",
            "classifications": process_classifications(activity, CODELISTS_IDS_BY_NAME),
            "collaboration_type": CODES["collaboration_type"][
                activity["Donor Type"].strip()
            ],
            "finance_type": CODES["finance_type"][
                activity["Type Of Assistance"].strip()
            ],
            "aid_type": CODES["aid_type"][
                activity["Aid Modality"].strip()
            ],
            "activity_status": CODES["activity_status"][
                activity["Status"].strip()
            ],
            "tied_status": "5", # Assume everything is untied
            "flow_type": "10", # Assume everything is ODA
            "finances": process_transactions(activity, start_date, CODELISTS_IDS_BY_NAME),
            "forwardspends": forwardspends,
            "locations": process_locations(activity, LOCATIONS)
        }
        qactivity.create_activity(d)