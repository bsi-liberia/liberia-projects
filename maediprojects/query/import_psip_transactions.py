# -*- coding: UTF-8 -*-
from flask import flash
from maediprojects import models
from maediprojects.lib import codelists, util, xlsx_to_csv
from maediprojects.query import finances as qfinances
from maediprojects.extensions import db
import openpyxl
import os
from collections import defaultdict


def first_or_only(list_or_dict):
    if type(list_or_dict) == list:
        return list_or_dict[0]
    return list_or_dict


def make_transactions(activity, project_data):
    flash("""Updated {} (Project ID: {})""".format(activity.title, activity.id), "success")
    for row in project_data:
        data = {
            "activity_id": activity.id,
            "aid_type": activity.aid_type,
            "finance_type": activity.finance_type,
            "provider_org_id": activity.funding_organisations[0].id,
            "receiver_org_id": activity.implementing_organisations[0].id,
            "currency": u"USD",
            "currency_automatic": True,
            "currency_source": u"USD",
            "currency_rate": 1.0,
            "transaction_description": u"Imported from IFMIS",
            "classifications": {
                "mtef-sector": str(
                    first_or_only(activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
            }
        }
        if float(row["ORIGINAL_APPROPRIATION"]) != 0:
            data["classifications"] = {
                    "mtef-sector": str(
                        first_or_only(activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
                }
            data["transaction_type"] = u"C"
            data["transaction_date"] = util.fp_fy_to_date(
                fp=row["fiscalperiod"],
                fy=int(row["fy"][0:4]),
                start_end='start').date().isoformat()
            data["transaction_value_original"] = float(row["ORIGINAL_APPROPRIATION"])
            qfinances.add_finances(activity.id, data)
        if float(row["ALLOTMENT"]) != 0:
            data["classifications"] = {
                    "mtef-sector": str(first_or_only(
                        activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
                }
            data["transaction_type"] = u"99-A"
            data["transaction_date"] = util.fp_fy_to_date(
                fp=row["fiscalperiod"],
                fy=int(row["fy"][0:4]),
                start_end='start').date().isoformat()
            data["transaction_value_original"] = float(row["ALLOTMENT"])
            qfinances.add_finances(activity.id, data)
        if float(row["ACTUAL"]) != 0:
            data["classifications"] = {
                    "mtef-sector": str(first_or_only(
                        activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
                }
            data["transaction_type"] = u"D"
            data["transaction_date"] = util.fp_fy_to_date(
                fp=row["fiscalperiod"],
                fy=int(row["fy"][0:4]),
                start_end='end').date().isoformat()
            data["transaction_value_original"] = float(row["ACTUAL"])
            qfinances.add_finances(activity.id, data)



def import_transactions_from_upload(uploaded_file):
    data = xlsx_to_csv.getDataFromFile(
        uploaded_file.filename,
        uploaded_file.read(), 0, True)
    return import_transactions(data)


def import_transactions_from_file():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "..", "lib", "import_files", "psip-transactions.xlsx")
    data = xlsx_to_csv.getDataFromFile(
        file_path, open(file_path, "rb").read(), 0, True)
    return import_transactions(data)


def import_transactions(data):
    grouped_by_code=defaultdict(list)
    relevant_activities = list(map(lambda a: (a.code[0:4], a), models.Activity.query.filter(
        models.Activity.domestic_external==u'domestic',
        models.Activity.code!=u"").all()))
    for project_code, activity in relevant_activities:
        grouped_by_code[project_code].append(activity)

    data_by_project = defaultdict(list)
    for row in data:
        row["project_key"] = row["project"].zfill(4)
        data_by_project[row["project_key"]].append(row)

    updated_projects = 0

    for project_code, project_data in data_by_project.items():
        if project_code in grouped_by_code:
            print "Importing project code {}".format(project_code)
            if len(grouped_by_code[project_code])>1:
                print("MORE THAN ONE PROJECT MAPPED TO {}; SKIPPING".format(project_code))
            else:
                existing_activity = grouped_by_code[project_code][0]
                existing_transactions = existing_activity.finances
                for transaction in existing_transactions:
                    db.session.delete(transaction)
                db.session.commit()
                make_transactions(existing_activity, project_data)
                updated_projects += 1
    return updated_projects
