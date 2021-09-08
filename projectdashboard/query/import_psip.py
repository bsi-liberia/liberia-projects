# -*- coding: UTF-8 -*-

import os
import re
import datetime as dt
import csv as unicodecsv

from projectdashboard import models
from projectdashboard.lib import codelists, util
from projectdashboard.query import activity as qactivity
from projectdashboard.query import finances as qfinances
from projectdashboard.query import organisations as qorganisations


basedir = os.path.abspath(os.path.dirname(__file__))


def clean_string(_string):
    return _string


def preprocess_data(csv):
    def append_path(root, data):
        project = root.setdefault("{}".format(data["project_code"]),
                                  {"rows": [],
                                   "name": data["project_name"],
                                   "code": data["project_code"],
                                   "earliest_year": data["fy"],
                                   "latest_year": data["fy"],
                                   "activity_status": "3",
                                   "organisations": set([(data["ministry_code"], data["ministry_name"])]),
                                   "sectors": set([(data["sector_code"], data["sector_name"])])
                                   }
                                  )
        if (float(data["REVISED_APPROPRIATION"]) != 0) or (float(data["ACTUAL"]) != 0):
            if float(data["REVISED_APPROPRIATION"]) != 0:
                r = {
                    "fy": data["fy"],
                    "fiscalperiod": data["fiscalperiod"],
                    "ministry_name": data["ministry_name"],
                    "ministry_code": data["ministry_code"],
                    "sector_name": data["sector_name"],
                    "sector_code": data["sector_code"],
                    "transaction_type": "C",
                    "transaction_value": float(data["REVISED_APPROPRIATION"])
                }
                project["rows"].append(r)
            if float(data["ACTUAL"]) != 0:
                r = {
                    "fy": data["fy"],
                    "fiscalperiod": data["fiscalperiod"],
                    "ministry_name": data["ministry_name"],
                    "ministry_code": data["ministry_code"],
                    "sector_name": data["sector_name"],
                    "sector_code": data["sector_code"],
                    "transaction_type": "D",
                    "transaction_value": float(data["ACTUAL"])
                }
                project["rows"].append(r)
            project["organisations"].add(
                (data["ministry_code"], data["ministry_name"]))
            project["sectors"].add((data["sector_code"], data["sector_name"]))
            if data["fy"] < project["earliest_year"]:
                project["earliest_year"] = data["fy"]
            if data["fy"] > project["latest_year"]:
                project["latest_year"] = data["fy"]
            if data["fy"] == "20182019":
                project["activity_status"] = "2"
    root = {}
    for row in csv:
        append_path(root, row)
    return root.values()


def read_file(FILENAME=os.path.join(basedir, "..", "lib/import_files/", "psip_ministry_sector.csv")):
    f = open(FILENAME, "rb")
    csv = unicodecsv.DictReader(f)
    return preprocess_data(csv)


def nonempty_from_list(some_list):
    for item in some_list:
        if item.strip() != "":
            return item
    return ""


def get_date(date_value):
    date_value = date_value.strip()
    if re.match(r"^\d{5}$", date_value):  # Excel date like 43465
        temp = dt.datetime(1899, 12, 30)
        delta = dt.timedelta(days=int(date_value))
        return (temp+delta).date()
    if re.match(r"^\d{2}/\d{2}/\d{4}$", date_value):  # dd/mm/yyyy
        return dt.datetime.strptime(date_value, "%d/%m/%Y").date()
    if date_value == "":
        return dt.datetime.utcnow().date()
    raise Exception  # Warn of strangely formatted dates


CODES = {
    "collaboration_type": {
        "Multilateral": "4",
        "Bilateral": "1",
        "": "1"
    },
    "finance_type": {
        "Loan": "410",
        "Grant": "110",
        "": "110"
    },
    "aid_type": {
        "Trust Fund": "B03",
        "Budget Support": "A01",
        "Project/Program Aid": "C01",
        "Pool Fund": "B04",
        "": "C01"
    },
    "activity_status": {
        "Cancelled": "5",
        "Executing": "2",
        "On-going": "2",
        "Ratified": "91",
        "Signed": "92",
        "signed": "92",
        "Started": "2",
        "": "2"
    }
}


def clean_get_create_organisation(_name, _code=None):
    # Remove "\" character from string
    name = re.sub(r"\\", "", clean_string(_name.strip()))
    if _code is not None:
        org_from_code = qorganisations.get_organisation_by_code(_code)
        if org_from_code:
            return org_from_code
    return qorganisations.get_or_create_organisation(name)


def make_organisation(role, name, code=None):
    organisation_id = clean_get_create_organisation(name, code)
    activity_org = models.ActivityOrganisation()
    activity_org.organisation_id = organisation_id
    activity_org.role = role
    return activity_org


def tidy_amount(amount_value):
    amount_value = amount_value.strip()
    amount_value = re.sub(",", "", amount_value)
    if re.match(r"^\d*$", amount_value):  # 2000
        return (float(amount_value), "USD")
    elif re.match(r"^-\d*$", amount_value):  # -2000
        return (float(amount_value), "USD")
    elif re.match(r'(\d*\.\d*)', amount_value):
        return (float(amount_value), "USD")
    elif re.match(r"^(\d*)m (\D*)$", amount_value):  # 20m EUR
        result = re.match(r"^(\d*)m (\D*)$", amount_value).groups()
        return (float(result[0])*1000000, result[1].upper())
    elif re.match(r"^(\d*) (\D*)$", amount_value):  # 2000 EUR
        result = re.match(r"^(\d*) (\D*)$", amount_value).groups()
        return (float(result[0]), result[1].upper())


def process_transaction_classifications(row, CODELIST_IDS_BY_CODE):
    classifications = []
    cl = models.ActivityFinancesCodelistCode()
    cl.codelist_id = 'mtef-sector'
    cl.codelist_code_id = CODELIST_IDS_BY_CODE["mtef-sector"].get(
        row["sector_code"],
        CODELIST_IDS_BY_CODE["mtef-sector"][""])
    classifications.append(cl)
    return classifications


def process_transactions(activity, CODELIST_IDS_BY_CODE):
    transactions = []
    for row in activity["rows"]:
        tr = models.ActivityFinances()
        tr.transaction_date = util.fp_fy_to_date(row["fiscalperiod"],
                                                 int(row["fy"][0:4]), "end")
        tr.transaction_type = row["transaction_type"]
        tr.transaction_description = "{} {} FY{}, imported from IFMIS PSIP data".format(
            {"C": "Revised appropriation for", "D": "Actuals for"}[
                row["transaction_type"]],
            row["fiscalperiod"],
            row["fy"]
        )
        tr.transaction_value = row["transaction_value"]
        tr.currency = "USD"
        tr.provider_org_id = clean_get_create_organisation(
            "Government of Liberia")
        tr.receiver_org_id = clean_get_create_organisation(
            row["ministry_name"], row["ministry_code"]
        )
        tr.finance_type = CODES["finance_type"]["Grant"]
        # NB defaults to C01 Project!
        tr.aid_type = CODES["aid_type"][""]
        tr.classifications = process_transaction_classifications(
            row, CODELIST_IDS_BY_CODE)
        transactions.append(tr)
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
            if activity[col].strip() in ("", "-", "0"):
                continue
            mtef_year = int(re.match(r"MTEF (\d{4})/\d{4}", col).groups()[0])
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

    # FIXME decide whether to do this…
    # Make adjustments to start/end dates if there are MTEFs found
    #  outside of these dates
    # if first_mtef < start_date.fy:
    #    first = util.fq_fy_to_date(1, first_mtef, "start")
    # if last_mtef > end_date_fy:
    #    end_date = util.fq_fy_to_date(4, last_mtef, "end")

    return start_date, end_date, forwardspends


def process_classifications(activity, CODELIST_IDS):
    classifications = []
    for sector_code, sector_name in activity["sectors"]:
        cl = models.ActivityCodelistCode()
        cl.codelist_code_id = CODELIST_IDS["mtef-sector"].get(sector_code,
                                                              CODELIST_IDS["mtef-sector"][""])
        cl.percentage = 100.0/len(activity["sectors"])
        classifications.append(cl)
    return classifications


def import_file():
    data = read_file()
    print("There are {} projects found".format(len(data)))

    # Get codelists for lookup
    CODELISTS_BY_NAME = codelists.get_codelists_lookups_by_name()
    CODELISTS_IDS_BY_NAME = codelists.get_codelists_ids_by_name()
    CODELISTS_IDS = codelists.get_codelists_lookups()
    CODELIST_IDS_BY_CODE = codelists.get_codelists_lookups_by_code()

    for activity in data:
        start_date = util.fq_fy_to_date(
            1, int(activity["earliest_year"][0:4]), "start")
        end_date = util.fq_fy_to_date(
            4, int(activity["latest_year"][0:4]), "end")

        d = {
            "user_id": 1,  # FIXME
            "domestic_external": "domestic",
            "code": activity["code"],
            "title": clean_string(activity["name"]),
            "description": "",
            # "description": nonempty_from_list([
            #     activity["Project Description"].decode("utf-8"),
            #     activity["Objective"].decode("utf-8"),
            # ]),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reporting_org_id": qorganisations.get_or_create_organisation(
                "Government of Liberia"),
            "organisations": [
                make_organisation(4, org[1], org[0]) for org in activity["organisations"]
            ] + [(make_organisation(1, "Government of Liberia"))],
            "recipient_country_code": "LR",
            "classifications": process_classifications(activity, CODELIST_IDS_BY_CODE),
            # "collaboration_type": CODES["collaboration_type"][
            #           activity["Donor Type"].strip()
            #       ],
            "finance_type": CODES["finance_type"]["Grant"],
            "aid_type": CODES["aid_type"][""],
            "activity_status": activity["activity_status"],
            #        "tied_status": "5", # Assume everything is untied
            #        "flow_type": "10", # Assume everything is ODA
            "finances": process_transactions(activity, CODELIST_IDS_BY_CODE),
        }
        qactivity.create_activity(d)
