# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
import datetime
from maediprojects.query import activity as qactivity
from maediprojects.lib import xlsx_to_csv, util
from maediprojects.lib.spreadsheet_headers import headers, fr_headers, headers_transactions
from maediprojects.lib.codelist_helpers import codelists 
from maediprojects.lib.codelists import get_codelists_lookups
from io import BytesIO
import re
from generate_csv import activity_to_json, generate_disb_fys, activity_to_transactions_list
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.writer.excel import save_virtual_workbook
from flask import flash
from openpyxl.styles import Color, PatternFill, Font, Border
import xlrd

def guess_types(cell_value):
    if cell_value == None: return ""
    try:
        if float(cell_value) == int(float(cell_value)):
            return int(float(cell_value))
        return float(cell_value)
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(cell_value, "%Y-%m-%d").date()
    except ValueError:
        pass
    return cell_value

class xlsxDictWriter(object):
    def writesheet(self, worksheet_name):
        """Sheet names can be a maximum of 31 chars. This method
        also writes the header."""
        self.ws = self.wb.create_sheet(worksheet_name[0:30])
        self.writeheader()

    def writerow(self, row_data):
        """Write row, but only for those fields that appear in
        header mapping"""
        hm = self.header_mapping
        for column_header, cell in row_data.items():
            if column_header not in hm: continue
            column_letter = get_column_letter((hm[column_header]))
            self.ws.cell('%s%s'%(column_letter, (self.row_index))
                ).value = guess_types(cell)
        self.row_index += 1

    def writeheader(self):
        self.header_mapping.values()
        self.row_index = 1
        self.writerow(dict(map(
            lambda x: (x, x), self.header_mapping.keys()
        )))

    def delete_first_sheet(self):
        self.wb.remove(self.wb.worksheets[0])
        out = BytesIO()
        self.wb.save(out)
        return out

    def save(self):
        out = BytesIO()
        self.wb.save(out)
        return out

    def __init__(self, headers):
        self.wb = Workbook()
        ws = self.wb.worksheets[0]
        ws.title="Data"
        self.header_mapping = dict(
            map(lambda x: (x[1], x[0]), enumerate(headers, start=1)))

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

def process_transaction_classifications(activity):
    activity_classification = activity.classification_data["mtef-sector"]["entries"][0]
    classifications = []
    cl = models.ActivityFinancesCodelistCode()
    cl.codelist_id = 'mtef-sector'
    cl.codelist_code_id = activity_classification.codelist_code_id
    classifications.append(cl)
    return classifications

def get_data_from_header(column_name):
    pattern = "(\d*) Q(\d) \(D\)"
    result = re.match(pattern, column_name).groups()
    return (result[1], result[0])

def get_fy_fq_date(fq, fy):
    qtrs = {"1": "09-30",
            "2": "12-31",
            "3": "03-31",
            "4": "06-30"}
    if fq in ("3","4"):
        fy = int(fy)+1
    return "{}-{}".format(fy,qtrs[fq])

def process_transaction(activity, amount, currency, column_name):
    provider = activity.funding_organisations[0].id
    receiver = activity.implementing_organisations[0].id

    fq, fy = get_data_from_header(column_name)
    end_fq_date = get_fy_fq_date(fq, fy)

    disbursement = models.ActivityFinances()
    disbursement.transaction_date = datetime.datetime.strptime(end_fq_date,
        "%Y-%m-%d")
    disbursement.transaction_type = u"D"
    disbursement.transaction_description = u"Disbursement for Q{} FY{}, imported from AMCU template".format(
        fq, fy
    )
    disbursement.transaction_value = amount
    disbursement.currency = currency
    disbursement.provider_org_id = provider
    disbursement.receiver_org_id = receiver
    disbursement.finance_type = activity.finance_type
    disbursement.aid_type = activity.aid_type
    disbursement.classifications = process_transaction_classifications(activity)
    return disbursement

def import_xls(input_file, column_name=u"2018 Q1 (D)"):
    xl_workbook = xlrd.open_workbook(filename=input_file.filename,
        file_contents=input_file.read())
    num_sheets = len(xl_workbook.sheet_names())
    num_updated_activities = 0
    activity_id = None
    cl_lookups = get_codelists_lookups()
    try:
        for sheet_id in range(0,num_sheets):
            input_file.seek(0)
            data = xlsx_to_csv.getDataFromFile(
                input_file.filename, input_file.read(), sheet_id, True)
            for row in data: # each row is one ID
                if column_name not in row:
                    flash("The column {} containing financial data was not \
                    found in the uploaded spreadsheet!".format(column_name), "danger")
                    raise Exception
                if ((row[column_name] == "") or 
                    (float(row[column_name]) == 0) or
                    (float(row[column_name]) == "-")):
                    continue
                activity_id = row[u"ID"]
                activity = qactivity.get_activity(activity_id)
                if not activity:
                    flash("Warning, activity ID \"{}\" with title \"{}\" was not found in the system \
                        and was not imported! Please create this activity in the \
                        system before trying to import.".format(row[u'ID'], row[u'Activity Title']), "warning")
                    continue
                existing_activity = activity_to_json(activity, cl_lookups)
                row_value, row_currency = tidy_amount(row[column_name])

                #FIXME need to handle multiple currencies later... also handle this in process_transaction()
                difference = row_value-float(existing_activity.get(column_name, 0))
                if difference == 0:
                    continue
                activity.finances.append(
                    process_transaction(activity, difference, row_currency, column_name)
                )
                db.session.add(activity)
                num_updated_activities += 1

                if existing_activity.get(column_name):
                    flash("Updated {} for {} (Project ID: {}); previous value was {}; \
                        new value is {}. New entry for {} added.".format(
                    util.column_data_to_string(column_name),
                    activity.title, activity.id,
                    existing_activity.get(column_name),
                    row.get(column_name),
                    difference
                    ), "success")
                else:
                    flash("Updated {} for {} (Project ID: {})".format(
                    util.column_data_to_string(column_name),
                    activity.title, activity.id), "success")
    except Exception, e:
        if activity_id:
            flash("""There was an unexpected error when importing your
            projects, there appears to be an error around activity ID {}. 
            The error was: {}""".format(activity_id, e), "danger")
        else:
            flash("""There was an unexpected error when importing your projects, 
        the error was: {}""".format(e), "danger")
    db.session.commit()
    return num_updated_activities

def generate_xlsx(filter_key=None, filter_value=None):
    disbFYs = generate_disb_fys()
    _headers = headers + disbFYs
    writer = xlsxDictWriter(_headers)
    writer.writesheet("Data")
    writer.writeheader()
    cl_lookups = get_codelists_lookups()
    if (filter_key and filter_value):
        activities = qactivity.list_activities_by_filters(
            {filter_key: filter_value})
    else:
        activities = qactivity.list_activities()
    for activity in activities:
        writer.writerow(activity_to_json(activity, cl_lookups))
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_filtered(arguments):
    disbFYs = generate_disb_fys()
    _headers = headers + disbFYs
    writer = xlsxDictWriter(_headers)
    writer.writesheet("Data")
    writer.writeheader()
    cl_lookups = get_codelists_lookups()
    if (arguments):
        activities = qactivity.list_activities_by_filters(
            arguments)
    else:
        activities = qactivity.list_activities()
    for activity in activities:
        writer.writerow(activity_to_json(activity, cl_lookups))
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_export_template(data):
    _headers = ["ID", "Project code", "Activity Title", util.previous_fy_fq()]
    writer = xlsxDictWriter(_headers)
    cl_lookups = get_codelists_lookups()

    myFill = PatternFill(start_color='FFFF00',
                         end_color='FFFF00',
                         fill_type = 'solid')

    for org_code, activities in sorted(data.items()):
        writer.writesheet(org_code)
        for activity in activities:
            writer.writerow(activity_to_json(activity, cl_lookups))
        writer.ws.column_dimensions[u"C"].width = 90
        writer.ws.column_dimensions[u"D"].width = 15
        writer.ws.cell(row=1,column=4).fill = myFill
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_transactions(filter_key=None, filter_value=None):
    disbFYs = generate_disb_fys()
    writer = xlsxDictWriter(headers_transactions)
    writer.writesheet("Data")
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
