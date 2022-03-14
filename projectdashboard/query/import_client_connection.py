# -*- coding: UTF-8 -*-

import os
from collections import defaultdict
import datetime
import re
import difflib

from flask import flash
import openpyxl
import sqlalchemy as sa

from projectdashboard import models
from projectdashboard.lib import codelists, util, xlsx_to_csv
from projectdashboard.query import finances as qfinances
from projectdashboard.query import activity as qactivity
from projectdashboard.extensions import db
from projectdashboard.query.import_iati import get_or_create_fund_source


def first_or_only(list_or_dict):
    if type(list_or_dict) == list:
        return list_or_dict[0]
    return list_or_dict


def parse_cc_date(_date):
    return datetime.datetime.strptime(_date, "%d-%b-%Y")


def get_iati_identifier_match(iati_identifier, cc_projects):
    if iati_identifier == None: return None
    elif iati_identifier in cc_projects:
        return iati_identifier
    elif iati_identifier[6:] in cc_projects:
        return iati_identifier[6:]
    return None


def client_connection_project(project_code):
    return models.ClientConnectionData.query.filter_by(processed=False,
        project_code=project_code
        ).all()


def client_connection_projects():
    return db.session.query(
        models.ClientConnectionData.project_code,
        models.ClientConnectionData.project_title
        ).distinct(models.ClientConnectionData.project_code
        ).order_by(models.ClientConnectionData.project_title
        ).all()


def make_finance_from_cc_transaction(activity, transaction):
    aF = models.ActivityFinances()
    aF.currency = 'USD'
    aF.transaction_date = transaction.transaction_date
    aF.transaction_type = 'D'
    aF.description = "Imported from Client Connection"
    aF.finance_type = {"grant": "110", "loan": "410"}[transaction.grant_loan]
    aF.aid_type = activity.aid_type
    aF.provider_org_id = activity.funding_organisations[0].id
    aF.receiver_org_id = activity.implementing_organisations[0].id
    aF.transaction_value_original = transaction.value
    aF.fund_source_id = get_or_create_fund_source(transaction.loan_number,
        aF.finance_type,
        transaction.loan_number)
    aFC = models.ActivityFinancesCodelistCode()
    aFC.codelist_id = 'mtef-sector'
    aFC.codelist_code_id = first_or_only(
        activity.classification_data["mtef-sector"]["entries"]).codelist_code_id
    aF.classifications = [aFC]
    aF.activity_id = activity.id
    aF.currency_source, aF.currency_rate, aF.currency_value_date = 'USD', 1, transaction.transaction_date
    return aF


def make_cc_finances(activity, cc_project_code):
    cc_project_transactions = filter(lambda project: project.value != 0, client_connection_project(cc_project_code))
    return [make_finance_from_cc_transaction(activity, transaction)
        for transaction in cc_project_transactions]


def combined_forwardspends(forwardspends):
    out = {}
    for forwardspend in forwardspends:
        if forwardspend.period_start_date not in out:
            out[forwardspend.period_start_date] = models.ActivityForwardSpend()
            out[forwardspend.period_start_date].period_start_date = forwardspend.period_start_date
            out[forwardspend.period_start_date].period_end_date = forwardspend.period_end_date
            out[forwardspend.period_start_date].value_date = forwardspend.value_date
            out[forwardspend.period_start_date].value_currency = 'USD'
            out[forwardspend.period_start_date].value = 0
        out[forwardspend.period_start_date].value += forwardspend.value
    return list(out.values())


def import_all_data():
    # Get list of WB activities with WB project ID
    # check project ID actually exists
    activities = models.Activity.query.filter(
        models.Activity.iati_identifier.isnot(None),
        models.Activity.iati_identifier.isnot(''),
        models.Activity.reporting_org_id == 11).all()
    ids_identifiers = [(activity.id, activity.iati_identifier) for activity in activities]
    iati_identifiers = [iati_identifier for activity_id, iati_identifier in ids_identifiers]
    status = []
    for activity_id, iati_identifier in ids_identifiers:
        if iati_identifiers.count(iati_identifier) != 1:
            status.append("Skipping activity {} as identifier {} appears more than once".format(activity_id, iati_identifier))
            continue
        print("Importing activity {} with identifier {}".format(activity_id, iati_identifier))
        result = import_data(iati_identifier, [activity_id], {})
        status.append("Updated activity {} (ID: {}); {} transactions before; {} transactions after import.".format(
            result['title'], result['id'], result['transactions_before'], result['transactions_after']))
    return status



def import_data(cc_project_code, activity_ids, activities_fields_options):
    activity = qactivity.get_activity(activity_ids[0])
    activity_id = activity.id
    activities = [qactivity.get_activity(
        _activity_id) for _activity_id in activity_ids]
    activities_lookup = dict((_activity.id, _activity)
                             for _activity in activities)
    activities_finances = [_finance for _activity in activities_lookup.values(
        ) for _finance in _activity.finances]

    transactions_before = len(activities_finances)

    activity_retained_finances = list(
        filter(lambda transaction: transaction.transaction_type == 'C', activities_finances))

    cc_finances = make_cc_finances(activity, cc_project_code)
    activity.finances = cc_finances + activity_retained_finances


    forwardspends = combined_forwardspends(_forwardspend for _activity in activities_lookup.values(
        ) for _forwardspend in _activity.forwardspends)

    activity.forwardspends = []

    db.session.add(activity)
    db.session.commit()

    # Set data from other activity (if we are merging activities)
    for field, field_activity_id in activities_fields_options.items():
        if field_activity_id == activity_id:
            continue
        field_data = getattr(qactivity.get_activity(field_activity_id), field)
        setattr(activity, field, field_data)

    for delete_id in activity_ids:
        # We don't delete the activity that we are merging
        if delete_id == activity_id:
            continue
        delete_activity = qactivity.get_activity(delete_id)
        db.session.delete(delete_activity)

    activity.forwardspends = forwardspends

    transactions_after = len(activity.finances)

    db.session.add(activity)
    db.session.commit()

    return {
        'id': activity.id,
        'title': activity.title,
        'transactions_before': transactions_before,
        'transactions_after': transactions_after}



def closest_matches_groupings():
    client_connection_projects = db.session.query(
        models.ClientConnectionData.project_code,
        models.ClientConnectionData.project_title
        ).distinct(models.ClientConnectionData.project_code
        ).order_by(models.ClientConnectionData.project_code
        ).all()

    #FIXME use some other identifier for WB?
    activities = models.Activity.query.filter_by(
        reporting_org_id=11
    ).with_entities(models.Activity.id, models.Activity.title, models.Activity.iati_identifier
                    ).all()
    activity_titles = [client_connection_project.project_title for client_connection_project in client_connection_projects]
    cc_projects_by_code = dict([(cc_project.project_code, cc_project.project_title) for cc_project in client_connection_projects])
    out = {}
    for activity in activities:
        title_orders = difflib.get_close_matches(
            activity.title, activity_titles, 1, 0.4)
        check_match_iati_identifier = get_iati_identifier_match(activity.iati_identifier, cc_projects_by_code.keys())
        if check_match_iati_identifier:
            cc_code = check_match_iati_identifier
            cc_title = cc_projects_by_code.get(check_match_iati_identifier)
        elif len(title_orders) > 0:
            cc_title = title_orders[0]
            cc_code = client_connection_projects[activity_titles.index(cc_title)].project_code
        else:
            cc_title = None
            cc_code = None
        out[activity.id] = {
            'id': activity.id,
            'iati_identifier': activity.iati_identifier,
            'title': activity.title,
            'client_connection_project_title': cc_title,
            'client_connection_project_code': cc_code
        }
    return out


def get_grant_loan(loan_number):
    if loan_number.startswith("TF"):
        return "grant"
    elif loan_number.startswith("IDA D"):
        return "grant"
    elif loan_number.startswith("IDA H"):
        return "grant"
    elif loan_number.startswith("IDA V"):
        return "loan"
    elif loan_number.startswith("IDA"):
        return "loan"
    return "unknown"


def add_row(filename, period_start, period_end, transaction):
    cc = models.ClientConnectionData()
    cc.filename = filename
    cc.period_start = period_start
    cc.period_end = period_end
    cc.project_code, cc.project_title = re.match(r'(\w*): (.*)', transaction['Project']).groups()
    cc.loan_number = transaction['Loan']
    cc.loan_currency = transaction['Currency of Loan Commitment']
    cc.grant_loan = get_grant_loan(transaction['Loan'])
    cc.transaction_date = datetime.datetime.strptime(transaction['EOP Date'], '%d-%b-%Y')
    cc.value = transaction['Disbursed During Month']
    cc.processed = False
    db.session.add(cc)
    db.session.commit()


def load_transactions_from_file(input_file):
    workbook = openpyxl.load_workbook(filename=input_file,
        read_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    fromto_cell = sheet['A5'].value
    _period_start, _period_end = re.match("(?:.*) from (.*) to (.*)", fromto_cell).groups()
    period_start = datetime.datetime.strptime(_period_start, '%d-%b-%Y')
    period_end = datetime.datetime.strptime(_period_end, '%d-%b-%Y')
    input_file.seek(0)
    data = xlsx_to_csv.getDataFromFile(
        input_file.filename, input_file.read(), 0, True, 5)
    for transaction in data:
        if transaction['Project'] == None: break
        try:
            add_row(input_file.filename, period_start, period_end, transaction)
        except sa.exc.IntegrityError:
            db.session.rollback()
            continue


def make_transactions(activity, project_data, fiscal_year=None, fund_sources={}):
    flash("""Updated {} (Project ID: {})""".format(
        activity.title, activity.id), "success")
    for row in project_data:

        data = {
            "activity_id": activity.id,
            "aid_type": activity.aid_type,
            "finance_type": fund_sources.get(row['Loan']).finance_type,
            "fund_source_id": fund_sources.get(row['Loan']).id,
            "provider_org_id": activity.funding_organisations[0].id,
            "receiver_org_id": activity.implementing_organisations[0].id,
            "currency": row["Currency of Loan Commitment"],
            "currency_automatic": True,
            "transaction_description": u"Imported from Client Connection",
            "classifications": {
                "mtef-sector": str(
                    first_or_only(activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
            }
        }
        # if (fiscal_year and (fiscal_year != row["fy"])):
        #    continue
        if float(row["Disbursed During Month"]) != 0:
            data["classifications"] = {
                "mtef-sector": str(first_or_only(
                    activity.classification_data["mtef-sector"]["entries"]).codelist_code_id)
            }
            data["transaction_type"] = u"D"
            data["transaction_date"] = parse_cc_date(
                row["EOP Date"]).date().isoformat()
            data["transaction_value_original"] = float(
                row["Disbursed During Month"])
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
        fy_start_date = util.fq_fy_to_date(
            1, util.fy_fy_to_fy(fiscal_year), "start").date()
        fy_end_date = util.fq_fy_to_date(
            4, util.fy_fy_to_fy(fiscal_year), "end").date()
        ifmis_fiscal_year = util.fy_fy_to_fyfy_ifmis(fiscal_year)
    else:
        fy_start_date, fy_end_date, ifmis_fiscal_year = None, None, None

    fund_sources = models.FundSource.query.all()
    fund_source_codes = dict(map(lambda fs: (fs.code, fs), fund_sources))
    grouped_by_code = defaultdict(list)
    relevant_activities = list(map(lambda a: (a.code, a), models.Activity.query.filter(
        models.Activity.code == u"44000-P125574").all()))
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
            if len(grouped_by_code[project_code]) > 1:
                flash("Project {} was not imported, as more than one project is mapped to it.".format(
                    project_code), "danger")
            else:
                existing_activity = grouped_by_code[project_code][0]
                existing_transactions = existing_activity.finances

                fund_sources_cc = set(map(lambda f: f["Loan"], project_data))
                if not set([fs in fund_source_codes.keys() for fs in fund_sources_cc]) == set([True]):
                    flash("Missing fund sources (required: {}), could not import project data.".format(
                        fund_sources_cc), "danger")
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
