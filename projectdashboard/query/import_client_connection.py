# -*- coding: UTF-8 -*-
from flask import flash
from maediprojects import models
from maediprojects.lib import codelists, util, xlsx_to_csv
from maediprojects.query import finances as qfinances
from maediprojects.extensions import db
import openpyxl
import os
from collections import defaultdict
import datetime
from six import u as unicode


def first_or_only(list_or_dict):
    if type(list_or_dict) == list:
        return list_or_dict[0]
    return list_or_dict


def parse_cc_date(_date):
    return datetime.datetime.strptime(_date, "%d-%b-%Y")


def make_transactions(activity, project_data, fiscal_year=None, fund_sources={}):
    flash("""Updated {} (Project ID: {})""".format(activity.title, activity.id), "success")
    for row in project_data:

        data = {
            "activity_id": activity.id,
            "aid_type": activity.aid_type,
            "finance_type": fund_sources.get(row['Loan']).finance_type,
            "fund_source_id": fund_sources.get(row['Loan']).id,
            "provider_org_id": activity.funding_organisations[0].id,
            "receiver_org_id": activity.implementing_organisations[0].id,
            "currency": unicode(row["Currency of Loan Commitment"]),
            "currency_automatic": True,
            "transaction_description": u"Imported from Client Connection",
            "classifications": {
                "mtef-sector": str(
                    first_or_only(activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
            }
        }
        #if (fiscal_year and (fiscal_year != row["fy"])):
        #    continue
        if float(row["Disbursed During Month"]) != 0:
            data["classifications"] = {
                    "mtef-sector": str(first_or_only(
                        activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
                }
            data["transaction_type"] = u"D"
            data["transaction_date"] = parse_cc_date(row["EOP Date"]).date().isoformat()
            data["transaction_value_original"] = float(row["Disbursed During Month"])
            qfinances.add_finances(activity.id, data)



def import_transactions_from_upload(uploaded_file, fiscal_year=None):
    data = xlsx_to_csv.getDataFromFile(
        uploaded_file.filename,
        uploaded_file.read(), 0, True)
    return import_transactions(data, fiscal_year)


def import_transactions_from_file(fiscal_year=None):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "..", "lib", "import_files", "WORLD BANK DISBURSEMENT.xlsx")
    data = xlsx_to_csv.getDataFromFile(
        file_path, open(file_path, "rb").read(), "all", True, 5)
    return import_transactions(data, 'FY2018/19')


def import_transactions(data, fiscal_year):
    if fiscal_year:
        fy_start_date = util.fq_fy_to_date(1, util.fy_fy_to_fy(fiscal_year), "start").date()
        fy_end_date = util.fq_fy_to_date(4, util.fy_fy_to_fy(fiscal_year), "end").date()
        ifmis_fiscal_year = util.fy_fy_to_fyfy_ifmis(fiscal_year)
    else:
        fy_start_date, fy_end_date, ifmis_fiscal_year = None, None, None

    fund_sources = models.FundSource.query.all()
    fund_source_codes = dict(map(lambda fs: (fs.code, fs), fund_sources))
    grouped_by_code=defaultdict(list)
    relevant_activities = list(map(lambda a: (a.code, a), models.Activity.query.filter(
        models.Activity.code==u"44000-P125574").all()))
    for project_code, activity in relevant_activities:
        grouped_by_code[project_code].append(activity)

    data_by_project = defaultdict(list)
    for row in data:
        row["project_key"] = "44000-{}".format(row["Project"].split(":")[0])
        data_by_project[row["project_key"]].append(row)

    updated_projects = 0

    for project_code, project_data in data_by_project.items():
        if project_code in grouped_by_code:
            print("Importing project code {}".format(project_code))
            if len(grouped_by_code[project_code])>1:
                flash("Project {} was not imported, as more than one project is mapped to it.".format(project_code), "danger")
            else:
                existing_activity = grouped_by_code[project_code][0]
                existing_transactions = existing_activity.finances

                fund_sources_cc = set(map(lambda f: f["Loan"], project_data))
                if not set([fs in fund_source_codes.keys() for fs in fund_sources_cc]) == set([True]):
                    flash("Missing fund sources (required: {}), could not import project data.".format(fund_sources_cc), "danger")
                    continue
                for transaction in existing_transactions:
                    if not fiscal_year:
                        db.session.delete(transaction)
                    elif (fiscal_year and
                        (transaction.transaction_date >= fy_start_date) and
                        (transaction.transaction_date <= fy_end_date)):
                        db.session.delete(transaction)
                db.session.commit()
                make_transactions(existing_activity, project_data,
                    ifmis_fiscal_year, fund_source_codes)
                updated_projects += 1
    return updated_projects
