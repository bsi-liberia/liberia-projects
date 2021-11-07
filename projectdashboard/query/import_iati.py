import datetime
from lxml import etree

from flask import current_app

from projectdashboard.query import activity as qactivity
from projectdashboard.query import finances as qfinances
from projectdashboard.query import exchangerates as qexchangerates
from projectdashboard.lib.codelist_helpers import codelists
from projectdashboard.lib.codelists import get_codelists_lookups
from projectdashboard.lib import util
from projectdashboard import models
from projectdashboard.extensions import db
import requests
from six import u as unicode
from iatiflattener.transaction import FlatIATITransaction
from iatiflattener.budget import FlatIATIBudget
from collections import namedtuple
import exchangerates


DATASTORE_URL = "https://datastore.codeforiati.org/api/1/access/activity.xml?iati-identifier={}"
DPORTAL_URL = "http://d-portal.org/q.xml?aid={}"
DSV1_IATI_IDENTIFIER_URL = "https://datastore.codeforiati.org/api/1/access/activity.xml?iati-identifier={}&limit=10"


def set_activity_iati_preferences(activity, iati_options):
    # Remove preferences that
    preferences = [
        pref for pref in activity.iati_preferences if pref.field in iati_options]
    preferences_found = [pref.field for pref in activity.iati_preferences]

    preferences += [models.ActivityIATIPreference(
        field) for field in iati_options if field not in preferences_found]
    return preferences


def update_imported_data():
    activities = models.Activity.query.join(
        models.ActivityIATIPreference).all()
    for activity in activities:
        import_options = {
            'commitments': 'dashboard',
            'disbursement': 'dashboard',
            'forwardspend': 'dashboard',
        }
        for iati_preference in activity.iati_preferences:
            import_options[iati_preference.field] = 'IATI'
        print("Import options are {}".format(import_options))

        print("Updating data for activity ID {} and IATI Identifier {}".format(
            activity.id,
            activity.iati_identifier))
        before_count_transactions = len(activity.finances)
        before_sum_disbursements = round(activity.total_disbursements)
        import_data(activity_id=activity.id,
                    iati_identifier=activity.iati_identifier,
                    activity_ids=[activity.id],
                    import_options=import_options,
                    activities_fields_options={})
        after_count_transactions = len(activity.finances)
        after_sum_disbursements = round(activity.total_disbursements)
        print("There were {} transactions before and {} transactions afterwards".format(
            before_count_transactions, after_count_transactions))
        print("There were USD {} disbursements before and USD {} disbursements afterwards".format(
            before_sum_disbursements, after_sum_disbursements))


def import_data(activity_id, iati_identifier, activity_ids, import_options, activities_fields_options):
    """
    Strategy:
    1. First get IATI data for this Identifier
    2. Get the IATI transactions summary for this Identifier
    3. Combine with any activity transactions that we should retain (from this other other activity_ids)
    4. Delete existing transactions and add new ones
    5. Combine other activity data
    6. Save import options to DB
    """
    activity = qactivity.get_activity(activity_id)
    activities = [qactivity.get_activity(
        _activity_id) for _activity_id in activity_ids]
    activities_lookup = dict((_activity.id, _activity)
                             for _activity in activities)
    iati_activity = retrieve_data(iati_identifier)
    #FIXME activity has disappeared, so we should unlink it
    if iati_activity is None: return False
    iati_activity_transactions = get_transactions_summary(iati_activity, False)
    iati_options = list(
        dict(filter(lambda option: option[1] == 'IATI', import_options.items())).keys())

    # Create IATI transactions
    iati_transaction_types = {
        '2': 'commitments',
        '3': 'disbursement',
        '4': 'disbursement'
    }

    def filter_iati_transactions(transaction):
        return iati_transaction_types.get(transaction["transaction_type"]) in iati_options
    iati_finances = makeFinancesFromTransactions(activity,
                                                 filter(filter_iati_transactions, iati_activity_transactions))

    db_transaction_types = {
        'C': 'commitments',
        'D': 'disbursement',
        'E': 'disbursement'
    }

    def filter_non_iati_transactions(finance):
        return db_transaction_types.get(finance.transaction_type) not in iati_options

    # Combine activity retained finances and IATI finances
    activities_finances = [_finance for _activity in activities_lookup.values(
    ) for _finance in _activity.finances]
    activity_retained_finances = list(
        filter(filter_non_iati_transactions, activities_finances))
    activity.finances = iati_finances + activity_retained_finances

    # Create IATI forward spends
    def filter_iati_forwardspends(transaction):
        if transaction["transaction_type"] != 'budget':
            return False
        return True
    if 'forwardspend' in iati_options:
        iati_forwardspends = makeForwardSpendsFromTransactions(activity,
                                                               aggregate_transactions(
                                                                   filter(
                                                                       filter_iati_forwardspends, iati_activity_transactions)
                                                               )['forwardspend']['data'])
        # For now, we clear activity.forwardspends
        # After commit(), we then add iati_forwardspends.
        # See below for more details of this.
        activity.forwardspends = []

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

    activity.iati_identifier = iati_identifier
    activity.iati_preferences = set_activity_iati_preferences(
        activity, iati_options)

    db.session.add(activity)
    db.session.commit()

    # https://github.com/sqlalchemy/sqlalchemy/issues/2501
    # We have to do this after an initial commit because otherwise we may get
    # an IntegrityError relating to a uniqueness constraint
    # if the new iati_forwardspends has activity_id and period_start_date
    # that already exists.
    if 'forwardspend' in iati_options:
        activity.forwardspends = iati_forwardspends
        db.session.add(activity)
        db.session.commit()

    return True


def makeForwardSpendFromTransaction(activity, transaction):
    fy = int(transaction['fiscal_year'])
    fq = int(transaction['fiscal_quarter'][1:])
    quarter_start_date = util.fq_fy_to_date(
        fq, fy, 'start', True
    )
    quarter_end_date = util.fq_fy_to_date(
        fq, fy, 'end', True
    )
    fs = models.ActivityForwardSpend()
    fs.value = round(transaction['value'], 2)
    fs.value_date = quarter_end_date
    fs.value_currency = 'USD'  # FIXME only USD currently handled
    fs.period_start_date = quarter_start_date
    fs.period_end_date = quarter_end_date
    return fs


def makeForwardSpendsFromTransactions(activity, transactions):
    return [makeForwardSpendFromTransaction(activity, transaction) for transaction in transactions]


def makeFinanceFromTransaction(activity, transaction):
    iati_transaction_types = {'2': 'C', '3': 'D', '4': 'D'}
    iati_finance_types = {'1': None, '2': None, '3': None, '4': None,
                          '110': '110', '111': '110', '210': None, '211': None, '310': None,
                          '311': None, '410': '410', '411': '410', '412': '410', '413': '410',
                          '414': '410', '421': '410', '422': '410', '423': '410', '424': '410',
                          '425': '410', '431': '410', '432': '410', '433': '410', '451': '410',
                          '452': '410', '453': '410', '510': None, '511': None, '512': None,
                          '520': None, '530': None, '610': None, '611': None, '612': None,
                          '613': None, '614': None, '615': None, '616': None, '617': None,
                          '618': None, '620': None, '621': None, '622': None, '623': None,
                          '624': None, '625': None, '626': None, '627': None, '630': None,
                          '631': None, '632': None, '633': None, '634': None, '635': None,
                          '636': None, '637': None, '638': None, '639': None, '710': None,
                          '711': None, '712': None, '810': None, '811': None, '910': None,
                          '911': None, '912': None, '913': None, '1100': None}
    iati_aid_types = {'A01': 'A01', 'A02': 'A02', 'B01': None, 'B02': None,
                      'B03': 'B03', 'B031': 'B03', 'B032': 'B03', 'B033': 'B03',
                      'B04': 'B04', 'C01': 'C01', 'D01': 'D01', 'D02': 'D01', 'E01': None,
                      'E02': None, 'F01': None, 'G01': None, 'H01': None, 'H02': None,
                      'H03': None, 'H04': None, 'H05': None}
    f = models.ActivityFinances()
    f.activity_id = activity.id
    f.currency = transaction['currency_original']
    f.transaction_date = util.isostring_date(transaction['transaction_date'])
    f.transaction_type = iati_transaction_types.get(
        transaction['transaction_type'])
    f.transaction_description = 'Imported from IATI data'

    f.finance_type = iati_finance_types.get(transaction['finance_type'])
    if (transaction['iati_identifier'].startswith('46002-')) and (f.finance_type == None):
        f.finance_type = '410'
    f.aid_type = iati_aid_types.get(transaction['aid_type'])
    f.provider_org_id = activity.funding_organisations[0].id
    f.receiver_org_id = activity.implementing_organisations[0].id
    aFC = models.ActivityFinancesCodelistCode()
    aFC.codelist_id = 'mtef-sector'
    aFC.codelist_code_id = first_or_only(
        activity.classification_data["mtef-sector"]["entries"]).codelist_code_id
    f.classifications = [aFC]
    # for AfDB we can take the fund source
    if transaction['iati_identifier'].startswith('46002-'):
        transaction_xml = transaction['transaction']
        nsmap = transaction_xml.nsmap
        if 'afdb' in nsmap:
            fund_source_code = transaction_xml.xpath(
                '@afdb:finance-type-id', namespaces=nsmap)
            fund_source_name = transaction_xml.find(
                "provider-org/narrative").text
            finance_type = iati_finance_types.get(transaction['finance_type'])
            if len(fund_source_code) == 0:
                fund_source_code = None
            else:
                fund_source_code = fund_source_code[0]
            if fund_source_code == '1': return None
            f.fund_source_id = get_or_create_fund_source(
                fund_source_name, finance_type, fund_source_code)
    f.transaction_value_original = transaction['value_original']
    f.value_date = transaction['value_date']
    f.currency_source, f.currency_rate, f.currency_value_date = qexchangerates.get_exchange_rate(
        f.value_date, f.currency)
    return f


def makeFinancesFromTransactions(activity, transactions):
    return list(filter(lambda transaction: transaction is not None, [makeFinanceFromTransaction(activity, transaction) for transaction in transactions]))


def retrieve_data(iati_identifier):
    r = requests.get(DSV1_IATI_IDENTIFIER_URL.format(iati_identifier))
    doc = etree.fromstring(r.text)
    activity = doc.find('.//iati-activity')
    return activity


def aggregate_transactions(transactions):
    grouped_transactions = {}

    def group_transaction_data(transaction, out):
        target = (
            transaction['fiscal_year'],
            transaction['fiscal_quarter'],
            transaction['transaction_type']
        )
        if target not in out:
            grouped_transactions[target] = 0.0
        grouped_transactions[target] += transaction['value_usd']
        return grouped_transactions
    for transaction in transactions:
        grouped_transactions = group_transaction_data(
            transaction, grouped_transactions)
    parts = list(map(lambda item: {
        'fiscal_year': item[0][0],
        'fiscal_quarter': item[0][1],
        'transaction_type': item[0][2],
        'value': item[1]
    }, grouped_transactions.items()))
    _parts = {'2': [], '3': [], 'budget': []}
    for part in parts:
        if part['transaction_type'] not in _parts:
            continue
        _parts[part['transaction_type']].append(part)
    return {
        'commitments': {
            'title': 'Commitments',
            'data': _parts['2']
        },
        'disbursement': {
            'title': 'Disbursements',
            'data': _parts['3']
        },
        'forwardspend': {
            'title': 'MTEF Projections',
            'data': _parts['budget']
        }
    }


def get_transactions_summary(activity, aggregated=True):
    flattener = namedtuple("FlattenIATIData",
                           ["activity_data", "organisations",
                            "category_group", "countries"])
    flattener.activity_data = {}
    flattener.organisations = {}
    flattener.category_group = {}
    flattener.countries = ['LR']
    flattener.exchange_rates = exchangerates.CurrencyConverter(
        update=False, source="consolidated-exchangerates.csv")

    transaction_parts = [transaction_part for transaction in
                         activity.findall("transaction") for transaction_part in FlatIATITransaction(
                             flattener, activity, transaction,
                             limit_transaction_types=False).flatten_transaction(as_dict=True)]

    budget_parts = [budget_part for budget_part in FlatIATIBudget(
        flattener, activity).flatten_budget(as_dict=True)]

    transaction_parts += budget_parts
    if aggregated:
        return aggregate_transactions(transaction_parts)
    return transaction_parts


def first_or_only(list_or_dict):
    if type(list_or_dict) == list:
        return list_or_dict[0]
    return list_or_dict


def get_or_create_fund_source(fund_source_name, finance_type, fund_source_code=None):
    if fund_source_code is None:
        fund_soure_code = fund_source_name
    fs = models.FundSource.query.filter_by(code=fund_source_code).first()
    if fs:
        if fs.finance_type != finance_type:
            fs.finance_type = finance_type
            db.session.add(fs)
            db.session.commit()
        return fs.id
    fs = models.FundSource()
    fs.code = fund_source_code
    fs.name = fund_source_name
    fs.finance_type = finance_type
    db.session.add(fs)
    db.session.commit()
    return fs.id


def process_transactions(iati_transactions, activity_transactions, activity_xml, activity):
    for transaction_xml in iati_transactions:
        aF = models.ActivityFinances()
        aF.currency = transaction_xml.find('value').get(
            'currency', activity_xml.get('default-currency'))
        aF.transaction_date = datetime.datetime.strptime(
            transaction_xml.find("transaction-date").get("iso-date"), "%Y-%m-%d")
        # Convert V2 to V1
        transaction_type = {'2': 'C', '3': 'D'}.get(
            transaction_xml.find("transaction-type").get("code"))
        if not transaction_type:
            continue
        aF.transaction_type = transaction_type
        if transaction_xml.find("description/narrative"):
            aF.description = "Imported from IATI - {}".format(
                transaction_xml.find("description/narrative").text)
        aF.finance_type = activity_xml.find("default-finance-type").get("code")
        aF.aid_type = activity_xml.find("default-aid-type").get("code")
        aF.provider_org_id = activity.funding_organisations[0].id
        aF.receiver_org_id = activity.implementing_organisations[0].id
        aF.transaction_value_original = transaction_xml.find("value").text
        aF.fund_source_id = get_or_create_fund_source(transaction_xml.find("provider-org/narrative").text,
                                                      activity_xml.find("default-finance-type").get("code"))
        aFC = models.ActivityFinancesCodelistCode()
        aFC.codelist_id = 'mtef-sector'
        aFC.codelist_code_id = first_or_only(
            activity.classification_data["mtef-sector"]["entries"]).codelist_code_id
        aF.classifications = [aFC]
        aF.activity_id = activity.id
        aF.currency_source, aF.currency_rate, aF.currency_value_date = qexchangerates.get_exchange_rate(
            transaction_xml.find("transaction-date").get("iso-date"), aF.currency)

        activity_transactions.append(aF)
    print("{} transactions".format(len(activity_transactions)))
    return activity_transactions


def process_documents(iati_documents, activity_documents):
    for document in iati_documents:
        if (document.get("url") in list(map(lambda d: d.url, activity_documents))): continue
        if document.find("document-date"):
            document_date = util.isostring_date(
                document.find("document-date").get("iso-date"))
        else:
            document_date = None
        d = models.ActivityDocumentLink()
        d.title = unicode(document.find("title/narrative").text)
        d.url = unicode(document.get("url"))
        d.categories = [models.ActivityDocumentLinkCategory(code=unicode(code)
                                                            ) for code in document.xpath("category/@code")]
        d.document_date = document_date
        activity_documents.append(d)
    return activity_documents


def process_results(iati_results, activity_results, activity_xml):
    for activity_result in activity_results:
        db.session.delete(activity_result)
    for result in iati_results:
        r = models.ActivityResult()
        r.result_title = unicode(result.find("title/narrative").text)
        r.result_type = result.get("type")
        for indicator in result.findall("indicator"):
            if activity_xml.find("reporting-org").get("ref") == "46002":
                i = models.ActivityResultIndicator()
                i.indicator_title = unicode(
                    result.find("title/narrative").text)
                i.measurement_type = {"1": u"Number", "2": u"Number"}.get(
                    indicator.get("measure"))
                i.measurement_unit_type = unicode(
                    indicator.find("title/narrative").text)
                p = models.ActivityResultIndicatorPeriod()
                p.period_start = datetime.datetime.strptime(
                    min(indicator.xpath("period/period-start/@iso-date")), "%Y-%m-%d")
                p.period_end = datetime.datetime.strptime(
                    max(indicator.xpath("period/period-end/@iso-date")), "%Y-%m-%d")
                p.target_value = unicode(indicator.find(
                    "period/target").get("value")) if indicator.find("period/target") is not None else None
                p.actual_value = unicode(indicator.find(
                    "period/actual").get("value")) if indicator.find("period/actual") is not None else None
                i.periods.append(p)
            else:
                i = models.ActivityResultIndicator()
                i.indicator_title = unicode(
                    indicator.find("title/narrative").text)
                i.baseline_year = datetime.date(year=int(indicator.find("baseline").get(
                    "year")), month=1, day=1) if indicator.find("baseline") else None
                i.baseline_value = unicode(indicator.find("baseline").get(
                    "value")) if indicator.find("baseline") else None
                i.measurement_type = {
                    "1": u"Number",
                    "2": u"Percentage",
                    "5": u"Yes/No"
                }.get(indicator.get("measure"))
                for period in indicator.findall("period"):
                    p = models.ActivityResultIndicatorPeriod()
                    p.period_start = datetime.datetime.strptime(
                        period.find("period-start").get("iso-date"), "%Y-%m-%d")
                    p.period_end = datetime.datetime.strptime(
                        period.find("period-end").get("iso-date"), "%Y-%m-%d")
                    p.target_value = unicode(period.find("target").get(
                        "value")) if period.find("target") is not None else None
                    p.actual_value = unicode(period.find("actual").get(
                        "value")) if period.find("actual") is not None else None
                    i.periods.append(p)
            r.indicators.append(i)
        activity_results.append(r)
    return activity_results


def process_activity(doc, activity, activity_code):
    if activity_code is not None:
        code = activity_code
    else:
        code = activity.code
    iati_documents = doc.xpath(
        "//iati-activity[iati-identifier='{}']/document-link".format(code))
    print("Found {} documents for activity {} with project code {}".format(
        len(iati_documents), activity.id, code))
    activity.documents = process_documents(iati_documents, [])

    iati_results = doc.xpath(
        "//iati-activity[iati-identifier='{}']/result".format(code))
    print("Found {} results for activity {} with project code {}".format(
        len(iati_results), activity.id, code))
    activity.results = process_results(iati_results, [], doc.xpath(
        "//iati-activity[iati-identifier='{}']".format(code))[0])

    #iati_transactions = doc.xpath("//iati-activity[iati-identifier='{}']/transaction".format(code))
    #print("Found {} transactions for activity {} with project code {}".format(len(iati_transactions), activity.id, code))

    # for activity_transaction in activity.finances:
    #    db.session.delete(activity_transaction)
    # db.session.commit()
    #activity.finances = process_transactions(iati_transactions, activity.finances, doc.xpath("//iati-activity[iati-identifier='{}']".format(code))[0], activity)

    db.session.add(activity)
    return len(iati_documents)


def import_documents(activity_id=None, activity_code=None):
    if activity_id is not None:
        activity = models.Activity.query.get(activity_id)
        r = requests.get(DPORTAL_URL.format(activity_code))
        doc = etree.fromstring(r.text)
        found_documents = process_activity(doc, activity, activity_code)
    else:
        activities = models.Activity.query.filter(
            models.Activity.domestic_external == u'external',
            models.Activity.code != u"").all()
        iati_identifiers = set(map(lambda a: a.code, activities))
        r = requests.get(DATASTORE_URL.format("|".join(iati_identifiers)))
        doc = etree.fromstring(r.text)
        found_documents = 0
        for activity in activities:
            found_documents += process_activity(doc, activity, activity_code)
    db.session.commit()
    print("Found {} documents!".format(found_documents))
    return bool(found_documents)
