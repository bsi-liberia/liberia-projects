import datetime
from lxml import etree as et

from flask import current_app

from maediprojects.query import activity as qactivity
from maediprojects.query import finances as qfinances
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.lib.codelist_helpers import codelists
from maediprojects.lib.codelists import get_codelists_lookups
from maediprojects import models
from maediprojects.extensions import db
import requests


DATASTORE_URL = "http://datastore.iatistandard.org/api/1/access/activity.xml?iati-identifier={}"
DPORTAL_URL = "http://d-portal.org/q.xml?aid={}"


def first_or_only(list_or_dict):
    if type(list_or_dict) == list:
        return list_or_dict[0]
    return list_or_dict


def get_or_create_fund_source(fund_source_name, finance_type):
    fs = models.FundSource.query.filter_by(code=fund_source_name).first()
    if fs: return fs.id
    fs = models.FundSource()
    fs.code = fund_source_name
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
        transaction_type = {'2': 'C', '3': 'D'}.get(transaction_xml.find("transaction-type").get("code"))
        if not transaction_type: continue
        aF.transaction_type = transaction_type
        if transaction_xml.find("description/narrative"):
            aF.description = "Imported from IATI - {}".format(transaction_xml.find("description/narrative").text)
        aF.finance_type = activity_xml.find("default-finance-type").get("code")
        aF.aid_type = activity_xml.find("default-aid-type").get("code")
        aF.provider_org_id = activity.funding_organisations[0].id
        aF.receiver_org_id = activity.implementing_organisations[0].id
        aF.transaction_value_original = transaction_xml.find("value").text
        aF.fund_source_id = get_or_create_fund_source(transaction_xml.find("provider-org/narrative").text,
            activity_xml.find("default-finance-type").get("code"))
        aFC = models.ActivityFinancesCodelistCode()
        aFC.codelist_id = 'mtef-sector'
        aFC.codelist_code_id = first_or_only(activity.classification_data["mtef-sector"]["entries"]).codelist_code_id
        aF.classifications = [aFC]
        aF.activity_id=activity.id
        aF.currency_source, aF.currency_rate, aF.currency_value_date = qexchangerates.get_exchange_rate(
        transaction_xml.find("transaction-date").get("iso-date"), aF.currency)

        activity_transactions.append(aF)
    print("{} transactions".format(len(activity_transactions)))
    return activity_transactions


def process_documents(iati_documents, activity_documents):
    for document in iati_documents:
        if (document.get("url") in list(map(lambda d: d.url, activity_documents))): continue
        if document.find("document-date"):
            document_date = util.isostring_date(document.find("document-date").get("iso-date"))
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
                i.indicator_title = unicode(result.find("title/narrative").text)
                i.measurement_type = {"1": u"Number", "2": u"Number"}.get(indicator.get("measure"))
                i.measurement_unit_type = unicode(indicator.find("title/narrative").text)
                p = models.ActivityResultIndicatorPeriod()
                p.period_start = datetime.datetime.strptime(min(indicator.xpath("period/period-start/@iso-date")), "%Y-%m-%d")
                p.period_end = datetime.datetime.strptime(max(indicator.xpath("period/period-end/@iso-date")), "%Y-%m-%d")
                p.target_value = unicode(indicator.find("period/target").get("value")) if indicator.find("period/target") is not None else None
                p.actual_value = unicode(indicator.find("period/actual").get("value")) if indicator.find("period/actual") is not None else None
                i.periods.append(p)
            else:
                i = models.ActivityResultIndicator()
                i.indicator_title = unicode(indicator.find("title/narrative").text)
                i.baseline_year = datetime.date(year=int(indicator.find("baseline").get("year")), month=1, day=1)
                i.baseline_value = unicode(indicator.find("baseline").get("value"))
                i.measurement_type = {
                    "1": u"Number",
                    "2": u"Percentage",
                    "5": u"Yes/No"
                    }.get(indicator.get("measure"))
                for period in indicator.findall("period"):
                    p = models.ActivityResultIndicatorPeriod()
                    p.period_start = datetime.datetime.strptime(period.find("period-start").get("iso-date"), "%Y-%m-%d")
                    p.period_end = datetime.datetime.strptime(period.find("period-end").get("iso-date"), "%Y-%m-%d")
                    p.target_value = unicode(period.find("target").get("value")) if period.find("target") is not None else None
                    p.actual_value = unicode(period.find("actual").get("value")) if period.find("actual") is not None else None
                    i.periods.append(p)
            r.indicators.append(i)
        activity_results.append(r)
    return activity_results


def process_activity(doc, activity, activity_code):
    if activity_code is not None:
        code = activity_code
    else:
        code = activity.code
    iati_documents = doc.xpath("//iati-activity[iati-identifier='{}']/document-link".format(code))
    print("Found {} documents for activity {} with project code {}".format(len(iati_documents), activity.id, code))
    activity.documents = process_documents(iati_documents, activity.documents)

    iati_results = doc.xpath("//iati-activity[iati-identifier='{}']/result".format(code))
    print("Found {} results for activity {} with project code {}".format(len(iati_results), activity.id, code))
    activity.results = process_results(iati_results, activity.results, doc.xpath("//iati-activity[iati-identifier='{}']".format(code))[0])

    iati_transactions = doc.xpath("//iati-activity[iati-identifier='{}']/transaction".format(code))
    print("Found {} transactions for activity {} with project code {}".format(len(iati_transactions), activity.id, code))

    for activity_transaction in activity.finances:
        db.session.delete(activity_transaction)
    db.session.commit()
    activity.finances = process_transactions(iati_transactions, activity.finances, doc.xpath("//iati-activity[iati-identifier='{}']".format(code))[0], activity)

    db.session.add(activity)
    return len(iati_documents)


def import_documents(activity_id=None, activity_code=None):
    if activity_id is not None:
        activity = models.Activity.query.get(activity_id)
        r = requests.get(DPORTAL_URL.format(activity_code))
        doc = et.fromstring(r.text)
        found_documents = process_activity(doc, activity, activity_code)
    else:
        activities = models.Activity.query.filter(
            models.Activity.domestic_external==u'external',
            models.Activity.code != u"").all()
        iati_identifiers = set(map(lambda a: a.code, activities))
        r = requests.get(DATASTORE_URL.format("|".join(iati_identifiers)))
        doc = et.fromstring(r.text)
        found_documents = 0
        for activity in activities:
            found_documents += process_activity(doc, activity, activity_code)
    db.session.commit()
    print("Found {} documents!".format(found_documents))
    return bool(found_documents)
