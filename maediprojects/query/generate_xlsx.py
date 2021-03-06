# -*- coding: UTF-8 -*-

import datetime
import re
from flask import flash
from openpyxl.styles import Protection
import xlrd

from maediprojects import models
from maediprojects.extensions import db
from maediprojects.query import activity as qactivity
from maediprojects.query import finances as qfinances
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import organisations as qorganisations
from maediprojects.lib import xlsx_to_csv, util
from maediprojects.lib.spreadsheet_headers import headers, fr_headers, headers_transactions
from maediprojects.lib.spreadsheets.validation import v_status, v_id, v_date, v_number
from maediprojects.lib.spreadsheets.formatting import yellowFill, orangeFill
from maediprojects.lib.spreadsheets import apply_formatting, helpers, xlsx_writer
from maediprojects.lib.codelist_helpers import codelists
from maediprojects.lib.codelists import get_codelists_lookups, get_codelists_lookups_by_name
from generate_csv import activity_to_json, generate_disb_fys, activity_to_transactions_list


def tidy_amount(amount_value):
    amount_value = amount_value.strip()
    amount_value = re.sub(",", "", amount_value)
    if re.match(r'^-?\d*\.?\d*$', amount_value):  # 2000 or -2000
        return (float(amount_value), u"USD")
    elif re.match(r"^(\d*)m (\D*)$", amount_value):  # 20m EUR
        result = re.match(r"^(\d*)m (\D*)$", amount_value).groups()
        return (float(result[0])*1000000, unicode(result[1].upper()))
    elif re.match(r"^(\d*) (\D*)$", amount_value):  # 2000 EUR
        result = re.match(r"^(\d*) (\D*)$", amount_value).groups()
        return (float(result[0]), unicode(result[1].upper()))


def clean_value(amount_value):
    if amount_value.strip() in ("", "-"): return 0
    return float(amount_value.strip())


def process_transaction_classifications(activity):
    activity_classification = activity.classification_data["mtef-sector"]["entries"][0]
    classifications = []
    cl = models.ActivityFinancesCodelistCode()
    cl.codelist_id = 'mtef-sector'
    cl.codelist_code_id = activity_classification.codelist_code_id
    classifications.append(cl)
    return classifications

def process_transaction(activity, amount, currency, column_name):
    provider = activity.funding_organisations[0].id
    receiver = activity.implementing_organisations[0].id
    fq, fy = util.get_data_from_header(column_name)
    end_fq_date = util.fq_fy_to_date(int(fq), int(fy), "end")
    disbursement = models.ActivityFinances()
    disbursement.transaction_date = end_fq_date
    disbursement.transaction_type = u"D"
    disbursement.transaction_description = u"Disbursement for Q{} FY{}, imported from AMCU template".format(
        fq, fy
    )
    disbursement.currency = currency
    disbursement.currency_automatic = True
    disbursement.currency_source, disbursement.currency_rate, disbursement.currency_value_date = qexchangerates.get_exchange_rate(disbursement.transaction_date, disbursement.currency)
    disbursement.transaction_value_original = amount
    disbursement.provider_org_id = provider
    disbursement.receiver_org_id = receiver
    disbursement.finance_type = activity.finance_type
    disbursement.aid_type = activity.aid_type
    disbursement.classifications = process_transaction_classifications(activity)
    return disbursement

def update_activity_data(activity, existing_activity, row, codelists):
    updated = False
    start_date = datetime.datetime.strptime(row[u"Activity Dates (Start Date)"], "%d/%m/%Y").date()
    end_date = datetime.datetime.strptime(row[u"Activity Dates (End Date)"], "%d/%m/%Y").date()

    # The older templates did not contain these columns, so we return here if these
    # columns are not present, in order to avoid a key error
    if ((row.get(u"Activity Status") == None) or
        (row.get(u"Activity Dates (Start Date)") == None) or
        (row.get(u"Activity Dates (End Date)") == None)):
        return False
    if existing_activity[u"Activity Title"] != row[u"Activity Title"]:
        activity.title = row[u"Activity Title"].decode("utf-8")
        updated = True
    if ("Activity Description" in row) and (existing_activity[u"Activity Description"] != row[u"Activity Description"]):
        activity.description = row[u"Activity Description"].decode("utf-8")
        updated = True
    if ("Implemented by" in row) and (existing_activity[u"Implemented by"] != row[u"Implemented by"]):
        for organisation in activity.organisations:
            if organisation.role == 4:
                db.session.delete(organisation)
        activity.organisations.append(qorganisations.make_organisation(
            row[u"Implemented by"].decode("utf-8"), 4))
        updated = True
    if existing_activity[u"Activity Status"] != row[u"Activity Status"]:
        activity.activity_status = codelists["ActivityStatus"][row[u"Activity Status"]]
        updated = True
    if existing_activity[u"Activity Dates (Start Date)"] != start_date.isoformat():
        activity.start_date = start_date
        updated = True
    if existing_activity[u"Activity Dates (End Date)"] != end_date.isoformat():
        activity.end_date = end_date
        updated = True
    activity.forwardspends += qfinances.create_missing_forward_spends(start_date, end_date, activity.id)
    return updated

def parse_mtef_cols(currency, mtef_cols, existing_activity, row, activity_id):
    updated_years = []
    for mtef_year in mtef_cols:
        new_fy_value = clean_value(row[mtef_year])
        if u'Q' in mtef_year: # Quarterly MTEF projections
            _mtef_year_year, _mtef_year_quarter = re.match(r"(\d*) Q(\d*) \(MTEF\)", mtef_year).groups()
            existing_fy_value = float(existing_activity["{} Q{} (MTEF)".format(
                _mtef_year_year, _mtef_year_quarter)])

            new_fy_value_in_usd = qexchangerates.convert_from_currency(
                currency = currency,
                _date = datetime.datetime.utcnow().date(),
                value = new_fy_value)
            difference = new_fy_value_in_usd-existing_fy_value
            # We ignore differences < 1 USD, because this can be due to rounding errors
            # when we divided input data by 4.
            if round(difference) == 0:
                continue
            value = new_fy_value_in_usd
            year, quarter = util.lr_quarter_to_cal_quarter(int("{}".format(_mtef_year_year)), int(_mtef_year_quarter))
            inserted = qfinances.create_or_update_forwardspend(activity_id, quarter, year, value, u"USD")
            updated_years.append(u"FY{} Q{}".format(_mtef_year_year, _mtef_year_quarter))
        else: # Annual MTEF projections
            fy_start, fy_end = re.match(r"FY(\d*)/(\d*) \(MTEF\)", mtef_year).groups()
            existing_fy_value = sum([float(existing_activity["20{} Q1 (MTEF)".format(fy_start)]),
                float(existing_activity["20{} Q2 (MTEF)".format(fy_start)]),
                float(existing_activity["20{} Q3 (MTEF)".format(fy_start)]),
                float(existing_activity["20{} Q4 (MTEF)".format(fy_start)])])

            new_fy_value_in_usd = qexchangerates.convert_from_currency(
                currency = currency,
                _date = datetime.datetime.utcnow().date(),
                value = new_fy_value)
            difference = new_fy_value_in_usd-existing_fy_value
            # We ignore differences < 1 USD, because this can be due to rounding errors
            # when we divided input data by 4.
            if round(difference) == 0:
                continue
            # Create 1/4 of new_fy_value for each quarter in this FY
            value = round(new_fy_value_in_usd/4.0, 4)
            for _fq in [1,2,3,4]:
                year, quarter = util.lr_quarter_to_cal_quarter(int("20{}".format(fy_start)), _fq)
                inserted = qfinances.create_or_update_forwardspend(activity_id, quarter, year, value, u"USD")
            updated_years.append(u"FY{}/{}".format(fy_start, fy_end))
    return updated_years

def parse_counterpart_cols(counterpart_funding_cols, activity, row, activity_id):
    updated_counterpart_years = []
    for counterpart_year in counterpart_funding_cols:
        new_fy_value = clean_value(row[counterpart_year])
        cfy_start, cfy_end = re.match(r"FY(\d*)/(\d*) \(GoL counterpart fund request\)", counterpart_year).groups()
        existing_cfy_value = activity.FY_counterpart_funding_for_FY("20{}".format(cfy_start))
        difference = new_fy_value-existing_cfy_value
        if difference == 0:
            continue
        cf_date = util.fq_fy_to_date(1, int("20{}".format(cfy_start))).date()
        inserted = qcounterpart_funding.create_or_update_counterpart_funding(activity_id, cf_date, new_fy_value)
        updated_counterpart_years.append(u"FY{}/{}".format(cfy_start, cfy_end))
    return updated_counterpart_years

def parse_disbursement_cols(currency, disbursement_cols, activity, existing_activity, row):
    updated_disbursements = []
    for column_name in disbursement_cols:
        row_value = clean_value(row[column_name])
        fq, fy = util.get_data_from_header(column_name)
        column_date = util.fq_fy_to_date(int(fq), int(fy), "end")
        existing_value = float(existing_activity.get(column_name, 0))
        existing_value_same_currency = qexchangerates.convert_to_currency(
            currency = currency,
            _date = column_date,
            value = existing_value)
        difference = round(row_value - existing_value_same_currency, 4)
        if (round(difference) == 0):
            continue
        activity.finances.append(
            process_transaction(activity, difference, currency, column_name)
        )
        db.session.add(activity)
        if existing_activity.get(column_name, 0) != 0:
            # Non-zero financial values were previously provided and should be adjusted upwards/downwards
            updated_disbursements.append(u"{}; previous value was {}; \
                new value is {}; new entry for {} added".format(
            util.column_data_to_string(column_name),
            existing_value_same_currency,
            row_value,
            difference))
        else:
            # Financial values were not previously provided, and are now entered
            updated_disbursements.append(u"{}".format(
            util.column_data_to_string(column_name)))
    return updated_disbursements

def make_updated_info(updated, activity, num_updated_activities):
    if updated.get("mtef_years") or updated.get("counterpart_years") or updated.get("disbursements") or updated.get("activity"):
        num_updated_activities += 1
        qactivity.activity_updated(activity.id)
    else:
        return num_updated_activities
    msg = u"Updated {} (Project ID: {}): ".format(
            activity.title,
            activity.id)
    msgs = []
    if updated.get("activity"):
        msgs.append(u"updated activity data")
    if updated.get("mtef_years"):
        msgs.append(u"updated MTEF projections for {}".format(
            ", ".join(updated["mtef_years"])))
    if updated.get("counterpart_years"):
        msgs.append(u"updated counterpart funding for {}".format(
            ", ".join(updated["counterpart_years"])))
    if updated.get("disbursements"):
        msgs.append(u"updated disbursement data for {}".format(
            ", ".join(updated["disbursements"])))
    flash(msg + "; ".join(msgs), "success")
    return num_updated_activities

def import_xls_mtef(input_file):
    return import_xls_new(input_file, "mtef")

def import_xls(input_file, column_name):
    return import_xls_new(input_file, "disbursements", [column_name])

def import_xls_new(input_file, _type, disbursement_cols=[]):
    xl_workbook = xlrd.open_workbook(filename=input_file.filename,
        file_contents=input_file.read())
    num_sheets = len(xl_workbook.sheet_names())
    num_updated_activities = 0
    cl_lookups = get_codelists_lookups()
    cl_lookups_by_name = get_codelists_lookups_by_name()
    def filter_mtef(column):
        pattern = r"(.*) \(MTEF\)$"
        return re.match(pattern, column)
    def filter_counterpart(column):
        pattern = r"(.*) \(GoL counterpart fund request\)$"
        return re.match(pattern, column)
    if u"Instructions" in xl_workbook.sheet_names():
        currency = xl_workbook.sheet_by_name(u"Instructions").cell_value(5,2)
        begin_sheet = 1
    else:
        currency = u"USD"
        begin_sheet = 0
    try:
        for sheet_id in range(begin_sheet,num_sheets):
            input_file.seek(0)
            data = xlsx_to_csv.getDataFromFile(
                input_file.filename, input_file.read(), sheet_id, True)
            if _type == 'mtef':
                mtef_cols = filter(filter_mtef, data[0].keys())
                counterpart_funding_cols = filter(filter_counterpart, data[0].keys())
                if len(mtef_cols) == 0:
                    flash("No columns containing MTEF projections data \
                    were found in the uploaded spreadsheet!", "danger")
                    raise Exception
            elif _type == 'disbursements':
                for _column_name in disbursement_cols:
                    if _column_name not in data[0].keys():
                        flash(u"The column {} containing financial data was not \
                        found in the uploaded spreadsheet!".format(column_name), "danger")
                        raise Exception
            for row in data: # each row is one ID
                activity_id = row[u"ID"]
                activity = qactivity.get_activity(activity_id)
                if not activity:
                    flash("Warning, activity ID \"{}\" with title \"{}\" was not found in the system \
                        and was not imported! Please create this activity in the \
                        system before trying to import.".format(row[u'ID'], row[u'Activity Title']), "warning")
                    continue
                existing_activity = activity_to_json(activity, cl_lookups)
                if _type == 'mtef':
                    updated = {
                        'activity': update_activity_data(activity, existing_activity, row, cl_lookups_by_name),
                        # Parse MTEF projections columns
                        'mtef_years': parse_mtef_cols(currency, mtef_cols, existing_activity, row, activity_id),
                        # Parse counterpart funding columns
                        'counterpart_years': parse_counterpart_cols(counterpart_funding_cols, activity, row, activity_id),
                    }
                elif _type == 'disbursements':
                    updated = {
                        'activity': update_activity_data(activity, existing_activity, row, cl_lookups_by_name),
                        'disbursements': parse_disbursement_cols(currency, disbursement_cols, activity, existing_activity, row)
                    }
                # Mark activity as updated and inform user
                num_updated_activities = make_updated_info(updated, activity, num_updated_activities)
    except xlrd.xldate.XLDateNegative as e:
        flash(u"""There was an unexpected error when importing your projects,
        one of the dates in your sheet has a negative value: {}. Please check your sheet
        and try again.""".format(e), "danger")
    except Exception as e:
        if activity_id:
            flash("""There was an unexpected error when importing your
            projects, there appears to be an error around activity ID {}.
            The error was: {}""".format(activity_id, e), "danger")
        else:
            flash("""There was an unexpected error when importing your projects,
        the error was: {}""".format(e), "danger")
    db.session.commit()
    return num_updated_activities

def generate_xlsx_filtered(arguments={}):
    disbFYs = generate_disb_fys()
    _headers = headers + disbFYs
    writer = xlsx_writer.xlsxDictWriter(_headers)
    writer.writesheet(u"Data")
    writer.writeheader()
    cl_lookups = get_codelists_lookups()
    activities = qactivity.list_activities_by_filters(
        arguments)
    for activity in activities:
        for fundsource, fundsource_data in activity.disb_fund_sources.items():
            activity_data = activity_to_json(activity, cl_lookups)
            activity_data.update(dict(map(lambda d: (d, 0.00), list(generate_disb_fys()))))
            activity_data["Fund Source"] = fundsource
            # Add Disbursements data
            activity_data[u'Fund Source'] = fundsource
            if fundsource is not None and fundsource_data.get('finance_type'):
                activity_data[u'Finance Type (Type of Assistance)'] = fundsource_data.get('finance_type')
            if fundsource in activity.FY_disbursements_dict_fund_sources:
                activity_data.update(dict(map(lambda d: (d[0], d[1]["value"]), activity.FY_disbursements_dict_fund_sources[fundsource].items())))
            if fundsource in activity.FY_forward_spend_dict_fund_sources:
                activity_data.update(dict(map(lambda d: (d[0], d[1]["value"]), activity.FY_forward_spend_dict_fund_sources[fundsource].items())))
            writer.writerow(activity_data)
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_export_template(data, mtef=False, currency=u"USD", _headers=None):
    mtef_cols, counterpart_funding_cols, disb_cols, _headers = helpers.get_column_information(mtef, _headers)
    for required_field in [u"ID", u"Activity Status", u'Activity Dates (Start Date)', u'Activity Dates (End Date)']:
        if required_field not in _headers:
            flash("Error: the field `{}` is required in this export. Please adjust your selected fields and try again!".format(required_field), "danger")
            return False
    writer = xlsx_writer.xlsxDictWriter(_headers,
        _type={True: "mtef", False: "disbursements"}[mtef],
        template_currency=currency,
        instructions_sheet=True)
    cl_lookups = get_codelists_lookups()

    for org_code, activities in sorted(data.items()):
        writer.writesheet(org_code)
        writer.ws.add_data_validation(v_status)
        writer.ws.add_data_validation(v_date)
        writer.ws.add_data_validation(v_number)
        writer.ws.add_data_validation(v_id)
        #writer.ws.protection.sheet = True
        for activity in activities:
            existing_activity = activity_to_json(activity, cl_lookups)
            for mtef_year in mtef_cols:
                fy_start, fy_end = re.match(r"FY(\d*)/(\d*) \(MTEF\)", mtef_year).groups()
                existing_activity[mtef_year] = sum([float(existing_activity["20{} Q1 (MTEF)".format(fy_start)]),
                    float(existing_activity["20{} Q2 (MTEF)".format(fy_start)]),
                    float(existing_activity["20{} Q3 (MTEF)".format(fy_start)]),
                    float(existing_activity["20{} Q4 (MTEF)".format(fy_start)])])
                if writer.template_currency != u"USD":
                    # N.B.: we convert at (close to) today's date,
                    # because these are *projections* and we store in USD
                    existing_activity[mtef_year] = qexchangerates.convert_to_currency(
                        currency = writer.template_currency,
                        _date = datetime.datetime.utcnow().date(),
                        value = existing_activity[mtef_year])
            # Convert disbursement data to writer.template_currency
            for disb_year in disb_cols:
                if writer.template_currency != u"USD":
                    existing_activity[disb_year] = qexchangerates.convert_to_currency(
                        currency = writer.template_currency,
                        _date = util.get_real_date_from_header(disb_year, "end"),
                        value = existing_activity[disb_year])
            # Leave in USD always
            for counterpart_year in counterpart_funding_cols:
                cfy_start, cfy_end = re.match(r"FY(\d*)/(\d*) \(GoL counterpart fund request\)", counterpart_year).groups()
                existing_activity[counterpart_year] = activity.FY_counterpart_funding_for_FY("20{}".format(cfy_start))
            writer.writerow(existing_activity)
        # Formatting
        apply_formatting.formatting_validation(writer, len(activities), _headers, counterpart_funding_cols, mtef_cols, disb_cols)
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_transactions(filter_key=None, filter_value=None):
    disbFYs = generate_disb_fys()
    writer = xlsx_writer.xlsxDictWriter(headers_transactions)
    writer.writesheet(u"Data")
    writer.writeheader()
    cl_lookups = get_codelists_lookups()
    if (filter_key and filter_value):
        activities = qactivity.list_activities_by_filters(
            {filter_key: filter_value})
    else:
        activities = qactivity.list_activities()
    for activity in activities:
        for tr in activity_to_transactions_list(activity, cl_lookups):
            writer.writerow(tr)
    writer.delete_first_sheet()
    return writer.save()
