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


def process_activity(doc, activity, activity_code):
    if activity_code is not None:
        code = activity_code
    else:
        code = activity.code
    iati_documents = doc.xpath("//iati-activity[iati-identifier='{}']/document-link".format(code))
    print("Found {} documents for activity {} with project code {}".format(len(iati_documents), activity.id, code))
    activity.documents = process_documents(iati_documents, activity.documents)
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
