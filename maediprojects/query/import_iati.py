import datetime
from lxml import etree as et

from flask import current_app

from maediprojects.query import activity as qactivity
from maediprojects.lib.codelist_helpers import codelists
from maediprojects.lib.codelists import get_codelists_lookups
from maediprojects import models
from maediprojects.extensions import db
import requests


DATASTORE_URL = "http://datastore.iatistandard.org/api/1/access/activity.xml?iati-identifier={}"
DPORTAL_URL = "http://d-portal.org/q.xml?aid={}"


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
