from io import BytesIO
from maediprojects.lib import docx_helpers as docx
from maediprojects.query import activity as qactivity
from maediprojects.lib.codelists import get_codelists_lookups, get_codelists

def make_doc(activity_id):
    project_brief_file = BytesIO()
    codelists = get_codelists_lookups()
    activity = qactivity.get_activity(activity_id)
    document = docx.create_document()
    document.add_heading(activity.title, 1)
    document.add_heading("General Information", 2)
    descriptive_data = [
    ('Project Title', activity.title),
    ('LPD code', str(activity.id)),
    ('Donor Project Code', activity.code or ""),
    ('Project Description', activity.description or ""),
    ('Project Objectives', ''),
    ('Expected Deliverables', ''),
    ('Alignment to PAPD', ''),
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
    sectors_data = list(map(lambda sector: (sector["name"], ", ".join(list(map(lambda entry: entry["codelist_code"]["name"], sector["entries"])))), activity.classification_data_dict.values()))
    document = docx.rows_to_table(sectors_data, document)
    document.add_heading("Key Financing Information", 2)
    financing_info = [
    ('Project value/cost', "USD {:,.2f}".format(activity.total_commitments or 0.00)),
    ('Finance type', ", ".join(list(map(lambda ft: "{}: {}%".format(ft[0], ft[1]), activity.disb_finance_types.items())))),
    ('Aid type', codelists["AidType"][activity.aid_type]),
    ('Commitment Charge', ''),
    ('Service Charge', ''),
    ('Interest', ''),
    ('Maturity', ''),
    ('Grace Period', ''),
    ('Financial Contributors', ", ".join(list(map(lambda org: org.name, activity.funding_organisations)))),
    ]
    document = docx.rows_to_table(financing_info, document)
    document.add_heading("Counterpart Funding", 3)
    document.add_paragraph('Includes the RAP cost, bank service charge etc. - all types of GoL contribution specified in the project agreement.')
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
    document = docx.rows_to_table(effectiveness_conditions, document, ['Condition', 'Status', 'Note / Comment'])
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
    ('FY2021 (July 1 2020 to June 30 2021)', "USD {:,.2f}".format(fy2021), ''),
    ('FY21.5 (July 1 2021 to December 31 2021)', "USD {:,.2f}".format(fy21), ''),
    ('FY22 (January 1 2022 to December 31 2022)', "USD {:,.2f}".format(fy22), '')
    ]
    document = docx.rows_to_table(mtef_projections, document, ['Fiscal Year(s)', 'Amount', 'Note / Comment'])
    document.add_heading("Project Implementation Information", 2)
    project_implementation = [
    ('Project status', codelists["ActivityStatus"][activity.activity_status]),
    ('Project Disbursement', "USD {:,.2f}".format(activity.total_disbursements or 0.00)),
    ('Financial Management', ''),
    ('Implemented by', ", ".join(list(map(lambda org: org.name, activity.implementing_organisations)))),
    ('Implementation Issues / Challenges', ''),
    ]
    document = docx.rows_to_table(project_implementation, document)
    document.add_heading("Results achieved", 3)
    results = [
    ('', '', ''),
    ('', '', '')
    ]
    document = docx.rows_to_table(results, document, ['Result', 'Status', 'Note/Comment'])
    document.add_heading("Beneficiaries", 3)
    beneficiaries = [
    ('Direct project beneficiaries', ''),
    ('Location(s)', ", ".join(list(map(lambda l: l.locations.name, activity.locations)))),
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
