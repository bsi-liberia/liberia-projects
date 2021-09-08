from io import BytesIO
from collections import defaultdict

import sqlalchemy as sa
from sqlalchemy.sql import func

from projectdashboard.lib import docx_helpers as docx
from projectdashboard.query import activity as qactivity
from projectdashboard.query import aggregates as qaggregates
from projectdashboard.query import codelists as qcodelists
from projectdashboard.lib.codelists import get_codelists_lookups, get_codelists
from projectdashboard.extensions import db
from projectdashboard import models


def make_sector_doc(sector_code):
    sector_brief_file = BytesIO()
    sector = qcodelists.get_code_by_id('mtef-sector', sector_code)
    sector_totals = qaggregates.aggregate('reporting-org',
                                          req_filters=[
                                              models.CodelistCode.codelist_code == 'mtef-sector',
                                              models.CodelistCode.code == sector_code
                                          ],
                                          req_finances_joins=[
                                              models.ActivityFinancesCodelistCode,
                                              models.CodelistCode
                                          ],
                                          req_forwardspends_joins=[
                                              models.ActivityCodelistCode,
                                              models.CodelistCode
                                          ]
                                          )
    filtered_current_fy = list(
        filter(lambda entry: entry.fiscal_year == '2020', sector_totals))

    donors = {}
    for item in filtered_current_fy:
        if item.code not in donors:
            donors[item.code] = {
                'code': item.code,
                'name': item.name,
                'disbursements': 0.00,
                'forwardspends': 0.00
            }
        if item.transaction_type == 'D':
            donors[item.code]['disbursements'] = round(
                item.total_value/1000000)
        if item.transaction_type == 'FS':
            donors[item.code]['forwardspends'] = round(
                item.total_value/1000000)

    ongoing_query = db.session.query(
        func.sum(models.ActivityFinances.transaction_value).label("total_value")
    ).join(models.Activity
           ).join(models.ActivityFinancesCodelistCode
                  ).join(models.CodelistCode
                         ).filter(
        models.ActivityFinances.transaction_type == 'D',
        models.Activity.activity_status == 2,
        models.CodelistCode.codelist_code == 'mtef-sector',
        models.CodelistCode.code == sector_code
    ).scalar()
    ongoing = round(ongoing_query/1000000)

    filtered_current_fy_disb = list(
        filter(lambda item: item.transaction_type == 'D', filtered_current_fy))
    current_fy_disb = round(
        sum(map(lambda item: item.total_value, filtered_current_fy_disb))/1000000)

    filtered_current_fy_fs = list(
        filter(lambda item: item.transaction_type == 'FS', filtered_current_fy))
    current_fy_fs = round(
        sum(map(lambda item: item.total_value, filtered_current_fy_fs))/1000000)

    filtered_cumulative_d = list(
        filter(lambda item: item.transaction_type == 'D', sector_totals))
    cumulative_d = round(
        sum(map(lambda item: item.total_value, filtered_cumulative_d))/1000000)

    document = docx.Document("projectdashboard/lib/docx/template.docx")
    document.add_heading('{} Sector Brief'.format(sector.name), 1)
    document.add_heading("General Information", 2)

    # Sector donors
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Sector donors: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run(
        "Includes current fiscal year projected and actual disbursement information for donors operating in the sector (FY 2020/2021) July 1 2020 to June 30, 2021")
    font = run.font
    font.italic = True
    sector_donors = [(
        donor['name'],
        "USD {:,}m".format(donor['forwardspends']),
        "USD {:,}m".format(donor['disbursements'])
    ) for donor in donors.values()]
    docx.rows_to_table(sector_donors, document, [
                       'Donor', 'Amount Projected', 'Amount Disbursed'])

    # Sector portfolio value
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Sector portfolio value: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run(
        "Includes cumulative financial information about the sector")
    font = run.font
    font.italic = True
    sector_portfolio = [(
        "",
        "USD {:,}m".format(ongoing),
        "",
        "",
        "USD {:,}m".format(current_fy_disb),
        "USD {:,}m".format(current_fy_fs),
        "USD {:,}m".format(cumulative_d))
    ]
    docx.rows_to_table(sector_portfolio, document, ['Total PAPD Financing Cost', 'Total value of all ongoing projects', 'GOL budget allocation',
                       'PAPD financing Gap', 'Current Fiscal year projection', 'Current fiscal year disbursement', 'Cumulative Disbursement from FY12/13'])

    # Sector thematic
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Key Sector Thematic Areas (PAPD): ")
    font = run.font
    font.bold = True
    run = paragraph.add_run("Includes area of focus in the PAPD")
    font = run.font
    font.italic = True
    sector_thematic = [
        ("", ""),
        ("", ""),
        ("", ""),
    ]
    docx.rows_to_table(sector_thematic, document, ['Thematic area', 'Comment'])

    # Sector deliverables
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Key Expected deliverables: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run("Includes a summary of key expected deliverables ")
    font = run.font
    font.italic = True
    sector_deliverables = [
        ("", ""),
        ("", ""),
        ("", ""),
    ]
    docx.rows_to_table(sector_deliverables, document, [
                       'Key expected deliverable', 'Comment'])

    # Sector deliverables
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Key Results Achieved: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run("Includes a summary of key results achieved")
    font = run.font
    font.italic = True
    results_achieved = [
        ("", ""),
        ("", ""),
        ("", ""),
    ]
    docx.rows_to_table(results_achieved, document, [
                       'Results achieved', 'Comment'])

    # Sector thematic gap
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Sector thematic gap: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run(
        "Includes PAPD thematic areas still requiring funding")
    font = run.font
    font.italic = True
    thematic_gap = [
        ("", ""),
        ("", ""),
        ("", ""),
    ]
    docx.rows_to_table(thematic_gap, document, ['Thematic area', 'Comment'])

    # Issues and Challenges:
    paragraph = document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Issues and Challenges: ")
    font = run.font
    font.bold = True
    run = paragraph.add_run(
        "Includes a summary of key issues and challenges requiring action")
    font = run.font
    font.italic = True
    issues_challenges = [
        ("", ""),
        ("", ""),
        ("", ""),
    ]
    docx.rows_to_table(issues_challenges, document, [
                       'Issues/challenges', 'Status'])

    # Save
    document.save(sector_brief_file)
    return sector_brief_file


def make_doc(activity_id):
    project_brief_file = BytesIO()
    codelists = get_codelists_lookups()
    activity = qactivity.get_activity(activity_id)
    document = docx.Document("projectdashboard/lib/docx/template.docx")
    document.add_heading(activity.title, 1)
    document.add_heading("General Information", 2)
    descriptive_data = [
        ('Project Title', activity.title),
        ('LPD code', str(activity.id)),
        ('Donor Project Code', activity.code or ""),
        ('Project Description', activity.description or ""),
        ('Project Objectives', activity.objectives or ""),
        ('Expected Deliverables', activity.deliverables or ""),
        ('Alignment to PAPD', activity.papd_alignment or ""),
    ]
    docx.rows_to_table(descriptive_data, document)
    document.add_heading("Basic data", 2)
    basic_data = [
        ('Start date', activity.start_date.isoformat()),
        ('End date', activity.end_date.isoformat()),
        ('Last updated', activity.updated_date.date().isoformat())
    ]
    document = docx.rows_to_table(basic_data, document)
    document.add_heading("Sectors", 2)
    sectors_data = list(map(lambda sector: (sector["name"], ", ".join(list(map(
        lambda entry: entry["codelist_code"]["name"], sector["entries"])))), activity.classification_data_dict.values()))
    document = docx.rows_to_table(sectors_data, document)
    document.add_heading("Key Financing Information", 2)
    financing_info = [
        ('Project value/cost',
         "USD {:,.2f}".format(activity.total_commitments or 0.00)),
        ('Finance type', ", ".join(list(map(lambda ft: "{}: {}%".format(
            ft[0], ft[1]), activity.disb_finance_types.items())))),
        ('Aid type', codelists["AidType"][activity.aid_type]),
        ('Commitment Charge', ''),
        ('Service Charge', ''),
        ('Interest', ''),
        ('Maturity', ''),
        ('Grace Period', ''),
        ('Financial Contributors', ", ".join(
            list(map(lambda org: org.name, activity.funding_organisations)))),
    ]
    document = docx.rows_to_table(financing_info, document)
    document.add_heading("Counterpart Funding", 3)
    document.add_paragraph(
        'Includes the RAP cost, bank service charge etc. - all types of GoL contribution specified in the project agreement.')
    # FIXME use data from database once agreement on
    # data structure reached.
    counterpart_funding = [
        ('RAP Cost', '', '', '', '', '', ''),
        ('Bank Charge', '', '', '', '', '', ''),
        ('Reimbursable', '', '', '', '', '', ''),
        ('', '', '', '', '', '', ''),
        ('', '', '', '', '', '', ''),
        ('Total GoL Contribution', '', '', '', '', '', '')
    ]
    document = docx.rows_to_table(counterpart_funding, document,
                                  ['Item', 'Total Amount', 'Amount disbursed to date',
                                   'July 1 2020 - June 30 2021',
                                   'July 1 2021 - December 31 2021',
                                   'January 1 2022 - December 31 2022',
                                   'Note / Comment']
                                  )
    document.add_heading("Effectiveness Conditions", 3)
    effectiveness_conditions = [
        ('', '', ''),
        ('', '', '')
    ]
    document = docx.rows_to_table(effectiveness_conditions, document, [
                                  'Condition', 'Status', 'Note / Comment'])
    document.add_heading("MTEF Projections", 2)
    # FIXME don't hardcode this - use n+2 once
    # new fiscal years data model established.
    forwardspends = activity.FY_forward_spend_dict

    def sum_if_exists(list_of_quarters):
        _sum = 0.0
        for quarter in list_of_quarters:
            _sum += quarter.get('value')
        return _sum
    fy2021 = sum_if_exists((
        forwardspends.get('2020 Q1 (MTEF)', {'value': 0}),
        forwardspends.get('2020 Q2 (MTEF)', {'value': 0}),
        forwardspends.get('2020 Q3 (MTEF)', {'value': 0}),
        forwardspends.get('2020 Q4 (MTEF)', {'value': 0})
    ))
    fy21 = sum_if_exists((
        forwardspends.get('2021 Q1 (MTEF)', {'value': 0}),
        forwardspends.get('2021 Q2 (MTEF)', {'value': 0})
    ))
    fy22 = sum_if_exists((
        forwardspends.get('2021 Q3 (MTEF)', {'value': 0}),
        forwardspends.get('2021 Q4 (MTEF)', {'value': 0}),
        forwardspends.get('2022 Q1 (MTEF)', {'value': 0}),
        forwardspends.get('2022 Q1 (MTEF)', {'value': 0})
    ))
    mtef_projections = [
        ('FY2021 (July 1 2020 to June 30 2021)',
         "USD {:,.2f}".format(fy2021), ''),
        ('FY21.5 (July 1 2021 to December 31 2021)',
         "USD {:,.2f}".format(fy21), ''),
        ('FY22 (January 1 2022 to December 31 2022)',
         "USD {:,.2f}".format(fy22), '')
    ]
    document = docx.rows_to_table(mtef_projections, document, [
                                  'Fiscal Year(s)', 'Amount', 'Note / Comment'])
    document.add_heading("Project Implementation Information", 2)
    project_implementation = [
        ('Project status', codelists["ActivityStatus"]
         [activity.activity_status]),
        ('Project Disbursement', "USD {:,.2f}".format(
            activity.total_disbursements or 0.00)),
        ('Financial Management', ''),
        ('Implemented by', ", ".join(
            list(map(lambda org: org.name, activity.implementing_organisations)))),
        ('Implementation Issues / Challenges', ''),
    ]
    document = docx.rows_to_table(project_implementation, document)
    document.add_heading("Results achieved", 3)
    results = [
        ('', '', ''),
        ('', '', '')
    ]
    document = docx.rows_to_table(
        results, document, ['Result', 'Status', 'Note/Comment'])
    document.add_heading("Beneficiaries", 3)
    beneficiaries = [
        ('Direct project beneficiaries', ''),
        ('Location(s)', ", ".join(
            list(map(lambda l: l.locations.name, activity.locations)))),
    ]
    document = docx.rows_to_table(beneficiaries, document)
    document.add_heading("Administrative Details", 2)
    administrative_details = [
        ('Contacts', ''),
        ('Supporting documents links/names', ''),
    ]
    document = docx.rows_to_table(administrative_details, document)
    document.save(project_brief_file)
    return project_brief_file
