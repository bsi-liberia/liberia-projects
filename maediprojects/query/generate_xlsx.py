# -*- coding: UTF-8 -*-

import datetime
from io import BytesIO
import re
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from flask import flash
from openpyxl.styles import Color, PatternFill, Font, Border, Protection, Alignment
from openpyxl.styles.borders import Border, Side
import xlrd

from maediprojects import models
from maediprojects.extensions import db
from maediprojects.query import activity as qactivity
from maediprojects.query import finances as qfinances
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.lib import xlsx_to_csv, util
from maediprojects.lib.spreadsheet_headers import headers, fr_headers, headers_transactions
from maediprojects.lib.codelist_helpers import codelists
from maediprojects.lib.codelists import get_codelists_lookups, get_codelists_lookups_by_name
from generate_csv import activity_to_json, generate_disb_fys, activity_to_transactions_list


yellowFill = PatternFill(start_color='FFFF00',
                     end_color='FFFF00',
                     fill_type = 'solid')

orangeFill = PatternFill(start_color='F79646',
                     end_color='F79646',
                     fill_type = 'solid')


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
            self.ws['%s%s'%(column_letter, (self.row_index))] = guess_types(cell)
        self.row_index += 1

    def writeheader(self):
        self.header_mapping.values()
        self.row_index = 1
        self.writerow(dict(map(
            lambda x: (x, x), self.header_mapping.keys()
        )))
        for col in range(1, len(self.header_mapping)+1):
            self.ws['{}1'.format(
                get_column_letter(col)
            )].font = Font(bold=True)

    def delete_first_sheet(self):
        self.wb.remove(self.wb.worksheets[0])
        out = BytesIO()
        self.wb.save(out)
        return out

    def save(self):
        out = BytesIO()
        self.wb.save(out)
        return out

    def write_instructions_sheet(self):
        ws = self.wb.create_sheet(u"Instructions")
        ws["A1"] = u"Instructions"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = u"Thank you for providing your data to AMCU! Capturing high quality data is vitally important to strengthening aid effectiveness in Liberia."
        ws["A2"].font = Font(size=14)
        ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells("A2:K4")
        ws["A6"] = u"Currency"
        ws["A6"].font = Font(bold=True, size=14)
        ws["A7"] = u"Please provide your data in the currency stated above. Please contact AMCU if you would like this template in a different currency (your existing data will be exported in your desired currency to ensure consistency)."
        ws["A7"].font = Font(size=14)
        ws["A7"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells("A7:K10")
        ws["C6"] = self.template_currency
        ws["C6"].font = Font(size=14)
        yellow_fill = PatternFill(start_color='FFFF00',
                             end_color='FFFF00',
                             fill_type = 'solid')
        thin_border = Border(left=Side(style='thin'),
                     right=Side(style='thin'),
                     top=Side(style='thin'),
                     bottom=Side(style='thin'))

        ws["C6"].fill = yellow_fill
        ws["C6"].border = thin_border
        ws["A12"] = u"How to fill in this template"
        ws["A12"].font = Font(bold=True, size=14)
        ws["A13"] = u"On the next sheet, you will see a list of projects currently known to AMCU. Fill out the sheet as follows (if you have any further questions, contact AMCU):"
        ws["A13"].font = Font(size=14)
        ws["A13"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells("A13:K15")
        if self._type == "mtef":
            ws["A16"] = u"Counterpart funding"
            ws["A16"].font = Font(size=14)
            ws["A16"].alignment = Alignment(vertical="top")
            ws["A16"].fill = orangeFill
            ws.row_dimensions[16].height=22
            ws.merge_cells("A16:C17")
            ws["D16"] = u"The amount that GoL has agreed to provide as counterpart funding for this project, for the coming Fiscal Year, in USD."
            ws["D16"].font = Font(size=14)
            ws["D16"].alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells("D16:K17")

            ws["A18"] = u"MTEF Projections"
            ws["A18"].font = Font(size=14)
            ws["A18"].fill = yellowFill
            ws.merge_cells("A18:C18")
            ws["D18"] = u"The amount you plan to spend in each of the next 3 Fiscal Years, in {}.".format(self.template_currency)
            ws["D18"].font = Font(size=14)
            ws.merge_cells("D18:K18")

            ws["A19"] = u"Other project data"
            ws["A19"].font = Font(size=14)
            ws.merge_cells("A19:C19")
            ws["D19"] = u"Please check other project data and update it as required."
            ws["D19"].font = Font(size=14)
            ws.merge_cells("D19:K19")

            ws["A20"] = u"New projects"
            ws["A20"].font = Font(size=14)
            ws["A20"].alignment = Alignment(vertical="top")
            ws.merge_cells("A20:C21")
            ws["D20"] = u"For new projects, add new rows at the bottom of the sheet. Leave the ID column blank."
            ws["D20"].font = Font(size=14)
            ws["D20"].alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[20].height=22
            ws.merge_cells("D20:K21")
        else:
            ws["A16"] = util.previous_fy_fq()
            ws["A16"].font = Font(size=14)
            ws["A16"].fill = yellowFill
            ws.merge_cells("A16:C16")
            ws["D16"] = u"The amount you spent on this project in the last fiscal quarter, in {}.".format(self.template_currency)
            ws["D16"].font = Font(size=14)
            ws.merge_cells("D16:K16")

            ws["A17"] = u"Other project data"
            ws["A17"].font = Font(size=14)
            ws.merge_cells("A17:C17")
            ws["D17"] = u"Please check other project data and update it as required."
            ws["D17"].font = Font(size=14)
            ws.merge_cells("D17:K17")

            ws["A18"] = u"New projects"
            ws["A18"].font = Font(size=14)
            ws["A18"].alignment = Alignment(vertical="top")
            ws.merge_cells("A18:C19")
            ws["D18"] = u"For new projects, add new rows at the bottom of the sheet. Leave the ID column blank."
            ws["D18"].font = Font(size=14)
            ws["D18"].alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[18].height=22
            ws.merge_cells("D18:K19")

        # Protect sheet
        ws.protection.sheet = True


    def __init__(self, headers, _type=u"disbursements",
            template_currency=u"USD",
            instructions_sheet=False):
        self.wb = Workbook()
        self.template_currency = template_currency
        self.instructions_sheet = instructions_sheet
        self._type = _type
        ws = self.wb.worksheets[0]
        ws.title = u"Data"
        if instructions_sheet:
            self.write_instructions_sheet()
        self.header_mapping = dict(
            map(lambda x: (x[1], x[0]), enumerate(headers, start=1)))

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
    end_fq_date = util.fq_fy_to_date(fq, fy, "end")

    disbursement = models.ActivityFinances()
    disbursement.transaction_date = datetime.datetime.strptime(end_fq_date,
        "%Y-%m-%d")
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

def import_xls_mtef(input_file):
    xl_workbook = xlrd.open_workbook(filename=input_file.filename,
        file_contents=input_file.read())
    num_sheets = len(xl_workbook.sheet_names())
    num_updated_activities = 0
    activity_id = None
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
            mtef_cols = filter(filter_mtef, data[0].keys())
            counterpart_funding_cols = filter(filter_counterpart, data[0].keys())
            if len(mtef_cols) == 0:
                flash("No columns containing MTEF projections data \
                were found in the uploaded spreadsheet!", "danger")
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
                updated_activity_data = update_activity_data(activity, existing_activity, row, cl_lookups_by_name)
                updated_years = []
                # Parse MTEF projections columns
                for mtef_year in mtef_cols:
                    new_fy_value = row[mtef_year]
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
                    # when we divided input date by 4.
                    if round(difference) == 0:
                        continue
                    # Create 1/4 of new_fy_value for each quarter in this FY
                    value = round(new_fy_value_in_usd/4.0, 4)
                    for _fq in [1,2,3,4]:
                        year, quarter = util.lr_quarter_to_cal_quarter(int("20{}".format(fy_start)), _fq)
                        inserted = qfinances.create_or_update_forwardspend(activity_id, quarter, year, value, u"USD")
                    updated_years.append(u"FY{}/{}".format(fy_start, fy_end))
                # Parse counterpart funding columns
                updated_counterpart_years = []
                for counterpart_year in counterpart_funding_cols:
                    new_fy_value = row[counterpart_year]
                    cfy_start, cfy_end = re.match(r"FY(\d*)/(\d*) \(GoL counterpart fund request\)", counterpart_year).groups()
                    existing_cfy_value = activity.FY_counterpart_funding_for_FY("20{}".format(cfy_start))
                    difference = new_fy_value-existing_cfy_value
                    if difference == 0:
                        continue
                    cf_date = util.fq_fy_to_date(1, int("20{}".format(cfy_start))).date()
                    inserted = qcounterpart_funding.create_or_update_counterpart_funding(activity_id, cf_date, new_fy_value)
                    updated_counterpart_years.append(u"FY{}/{}".format(cfy_start, cfy_end))
                if updated_years or updated_counterpart_years or updated_activity_data:
                    num_updated_activities += 1
                    qactivity.activity_updated(activity.id)
                if updated_years:
                    #FIXME there is an issue with a maximum number of flash messages
                    # so this sometimes breaks -- this is the reason we only display
                    # for MTEF updates as for these it is more important.
                    flash(u"Updated MTEF projections for {} for {} (Project ID: {})".format(
                        ", ".join(updated_years),
                        activity.title,
                        activity.id), "success")
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

def import_xls(input_file, column_name=u"2018 Q1 (D)"):
    xl_workbook = xlrd.open_workbook(filename=input_file.filename,
        file_contents=input_file.read())
    num_sheets = len(xl_workbook.sheet_names())
    num_updated_activities = 0
    activity_id = None
    cl_lookups = get_codelists_lookups()
    cl_lookups_by_name = get_codelists_lookups_by_name()
    if u"Instructions" in xl_workbook.sheet_names():
        currency = xl_workbook.sheet_by_name(u"Instructions").cell_value(5,2)
        begin_sheet = 1
    else:
        currency = u"USD"
        begin_sheet = 0
    try:
        for sheet_id in range(begin_sheet, num_sheets):
            input_file.seek(0)
            data = xlsx_to_csv.getDataFromFile(
                input_file.filename, input_file.read(), sheet_id, True)
            for row in data: # each row is one ID
                if column_name not in row:
                    flash(u"The column {} containing financial data was not \
                    found in the uploaded spreadsheet!".format(column_name), "danger")
                    raise Exception
                activity_id = row[u"ID"]
                activity = qactivity.get_activity(activity_id)
                if not activity:
                    flash(u"Warning, activity ID \"{}\" with title \"{}\" was not found in the system \
                        and was not imported! Please create this activity in the \
                        system before trying to import.".format(row[u'ID'], row[u'Activity Title']), "warning")
                    continue
                existing_activity = activity_to_json(activity, cl_lookups)
                row_value = row[column_name]
                updated_activity_data = update_activity_data(activity, existing_activity, row, cl_lookups_by_name)
                fq, fy = util.get_data_from_header(column_name)
                column_date = util.fq_fy_to_date(fq, fy, "end")
                existing_value = float(existing_activity.get(column_name, 0))
                existing_value_same_currency = qexchangerates.convert_to_currency(
                    currency = currency,
                    _date = column_date,
                    value = existing_value)
                difference = round(row_value - existing_value_same_currency, 4)
                if (round(difference) == 0) and (updated_activity_data == False):
                    continue
                if round(difference) != 0:
                    activity.finances.append(
                        process_transaction(activity, difference, currency, column_name)
                    )
                db.session.add(activity)
                num_updated_activities += 1
                qactivity.activity_updated(activity.id)

                if round(difference) == 0:
                    # Financial values not updated, only other activity data
                    flash(u"Updated {} (Project ID: {})".format(
                    activity.title, activity.id), "success")
                elif existing_activity.get(column_name, 0) != 0:
                    # Non-zero financial values were previously provided and should be adjusted upwards/downwards
                    flash(u"Updated {} for {} (Project ID: {}); previous value was {}; \
                        new value is {}. New entry for {} added.".format(
                    util.column_data_to_string(column_name),
                    activity.title, activity.id,
                    existing_value_same_currency,
                    row_value,
                    difference
                    ), "success")
                else:
                    # Financial values were not previously provided, and are now entered
                    flash(u"Updated {} for {} (Project ID: {})".format(
                    util.column_data_to_string(column_name),
                    activity.title, activity.id), "success")
    except Exception, e:
        if activity_id:
            flash(u"""There was an unexpected error when importing your
            projects, there appears to be an error around activity ID {}.
            The error was: {}""".format(activity_id, e), "danger")
        else:
            flash(u"""There was an unexpected error when importing your projects,
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
    writer.writesheet(u"Data")
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

def generate_xlsx_export_template(data, mtef=False, currency=u"USD"):
    if mtef:
        current_year = datetime.datetime.utcnow().date().year
        mtef_cols = [u"FY{}/{} (MTEF)".format(str(year)[2:4], str(year+1)[2:4]) for year in range(current_year, current_year+3)]
        counterpart_funding_cols = [u"FY{}/{} (GoL counterpart fund request)".format(str(year)[2:4], str(year+1)[2:4]) for year in range(current_year, current_year+1)]
        _headers = [u"ID", u"Project code", u"Activity Title"]
        _headers += counterpart_funding_cols
        _headers += mtef_cols
        _headers += [u'Activity Status', u'Activity Dates (Start Date)', u'Activity Dates (End Date)',
    u"County"]
    else:
        mtef_cols = []
        counterpart_funding_cols = []
        _headers = [u"ID", u"Project code", u"Activity Title", util.previous_fy_fq(),
    u'Activity Status', u'Activity Dates (Start Date)', u'Activity Dates (End Date)',
    u"County",]
    writer = xlsxDictWriter(_headers,
        _type={True: "mtef", False: "disbursements"}[mtef],
        template_currency=currency,
        instructions_sheet=True)
    cl_lookups = get_codelists_lookups()

    statuses = get_codelists_lookups_by_name()["ActivityStatus"].keys()

    # Activity Status validation
    v_status = DataValidation(type="list", formula1='"{}"'.format(u",".join(statuses)), allow_blank=False)
    v_status.error ='Your entry is not in the list'
    v_status.errorTitle = 'Activity Status'
    v_status.prompt = 'Please select from the list'
    v_status.promptTitle = 'Activity Status'

    v_id = DataValidation(type="whole")
    v_id.errorTitle = "Invalid ID"
    v_id.error = "Please enter a valid ID"
    v_id.promptTitle = 'Liberia Project Dashboard ID'
    v_id.prompt = 'Please do not edit this ID. It is used by the Liberia Project Dashboard to uniquely identify activities.'

    v_date = DataValidation(type="date")
    v_date.errorTitle = "Invalid date"
    v_date.error = "Please enter a valid date"

    v_number = DataValidation(type="decimal")
    v_number.errorTitle = "Invalid number"
    v_number.error = "Please enter a valid number"

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
            if writer.template_currency != u"USD":
                existing_activity[util.previous_fy_fq()] = qexchangerates.convert_to_currency(
                    currency = writer.template_currency,
                    _date = util.previous_fy_fq_date(),
                    value = existing_activity[util.previous_fy_fq()])
            # Leave in USD always
            for counterpart_year in counterpart_funding_cols:
                cfy_start, cfy_end = re.match(r"FY(\d*)/(\d*) \(GoL counterpart fund request\)", counterpart_year).groups()
                existing_activity[counterpart_year] = activity.FY_counterpart_funding_for_FY("20{}".format(cfy_start))
            writer.writerow(existing_activity)
        if mtef == True:
            for rownum in range(1+1, len(activities)+2):
                writer.ws.cell(row=rownum,column=4).fill = orangeFill
                writer.ws.cell(row=rownum,column=5).fill = yellowFill
                writer.ws.cell(row=rownum,column=6).fill = yellowFill
                writer.ws.cell(row=rownum,column=7).fill = yellowFill
                writer.ws.cell(row=rownum,column=4).number_format = u'"USD "#,##0.00'
                writer.ws.cell(row=rownum,column=5).number_format = u'"{} "#,##0.00'.format(writer.template_currency)
                writer.ws.cell(row=rownum,column=6).number_format = u'"{} "#,##0.00'.format(writer.template_currency)
                writer.ws.cell(row=rownum,column=7).number_format = u'"{} "#,##0.00'.format(writer.template_currency)
            writer.ws.column_dimensions[u"C"].width = 50
            writer.ws.column_dimensions[u"D"].width = 35
            writer.ws.column_dimensions[u"E"].width = 18
            writer.ws.column_dimensions[u"F"].width = 18
            writer.ws.column_dimensions[u"G"].width = 18
            writer.ws.column_dimensions[u"H"].width = 18
            writer.ws.column_dimensions[u"I"].width = 20
            writer.ws.column_dimensions[u"J"].width = 20
            v_id.add('A2:A{}'.format(len(activities)+2))
            v_number.add('D2:G{}'.format(len(activities)+2))
            v_status.add('H2:H{}'.format(len(activities)+2))
            v_date.add('I2:J{}'.format(len(activities)+2))
        elif mtef == False:
            for rownum in range(1+1, len(activities)+2):
                writer.ws.cell(row=rownum,column=4).fill = yellowFill
                writer.ws.cell(row=rownum,column=4).number_format = u'"{} "#,##0.00'.format(writer.template_currency)
            writer.ws.column_dimensions[u"C"].width = 70
            writer.ws.column_dimensions[u"D"].width = 18
            writer.ws.column_dimensions[u"E"].width = 18
            writer.ws.column_dimensions[u"F"].width = 20
            writer.ws.column_dimensions[u"G"].width = 20
            v_id.add('A2:A{}'.format(len(activities)+2))
            v_number.add('D2:D{}'.format(len(activities)+2))
            v_status.add('E2:E{}'.format(len(activities)+2))
            v_date.add('F2:G{}'.format(len(activities)+2))
    writer.delete_first_sheet()
    return writer.save()

def generate_xlsx_transactions(filter_key=None, filter_value=None):
    disbFYs = generate_disb_fys()
    writer = xlsxDictWriter(headers_transactions)
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
