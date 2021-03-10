from maediprojects.views.api import jsonify
from maediprojects.query import activity as qactivity
from maediprojects.query import user as quser
from maediprojects.query import import_iati as qimport_iati
from maediprojects.query import generate as qgenerate

from flask import Blueprint, request, \
    url_for, Response, current_app, abort

from flask_jwt_extended import (
    jwt_required
)
import re
import json
import requests
from lxml import etree
from urllib import parse as urllib_parse

#DSV2_SEARCH_URL = "https://iatidatastore.iatistandard.org/api/activities/?format=json&q=%22{}%22&recipient_country=LR&reporting_org_identifier={}&fields=iati_identifier,title,description"
#DSV2_IATI_IDENTIFIER_URL = "https://iatidatastore.iatistandard.org/api/activities/?format=json&iati_identifier={}&fields=iati_identifier,title,description"

DSV1_TITLE_URL = "https://datastore.codeforiati.org/api/1/access/activity.xml?title={}&reporting-org={}&limit=10"
DSV1_IATI_IDENTIFIER_URL = "https://datastore.codeforiati.org/api/1/access/activity.xml?iati-identifier={}&limit=10"

blueprint = Blueprint('iati', __name__, url_prefix='/api/iati')


def fix_narrative(ref, text):
    return text.strip()


def get_narrative(container):
    narratives = container.xpath("narrative")
    if len(narratives) == 0: return ""
    if len(narratives) == 1:
        if narratives[0].text:
            return fix_narrative(container.get('ref'), narratives[0].text.strip())
        else: return ""
    def filter_lang(element):
        lang = element.get("{http://www.w3.org/XML/1998/namespace}lang")
        return lang in (None, 'en')
    filtered = list(filter(filter_lang, narratives))
    if len(filtered) == 0: return fix_narrative(container.get('ref'), narratives[0].text.strip())
    return fix_narrative(container.get('ref'), filtered[0].text.strip())


@blueprint.route("/iati.json")
def api_list_iati_files():
    urls = qactivity.get_iati_list()
    return jsonify(urls = urls)


@blueprint.route("/<version>/<country_code>.xml")
def generate_iati_xml(version, country_code):
    if version == "1.03":
        xml = qgenerate.generate_103(country_code)
        return Response(xml, mimetype='text/xml')
    elif version == "2.01":
        xml = qgenerate.generate_201(country_code)
        return Response(xml, mimetype='text/xml')

    return "ERROR: UNKNOWN VERSION"


def urlencode_text(text):
    return urllib_parse.quote(text)


@blueprint.route("/search/", methods=["POST"])
@jwt_required()
def api_iati_search():
    args = request.get_json()
    title = args["title"]
    reporting_org_code = args["reporting_org_code"] # NB DSv2 uses "," rather than "|"
    def clean_data(doc):
        def clean_activity(activity):
            title = get_narrative(activity.find("title"))
            description = get_narrative(activity.find("description"))
            return {
                'iati_identifier': activity.find("iati-identifier").text,
                'title': title,
                'description': description
            }
        return {
            "results": list(map(lambda activity: clean_activity(activity), doc.xpath("//iati-activity")))
        }
    # Try to get IATI Identifier results
    if (args.get("iati_identifier")) and (args.get('iati_identifier').strip() != ''):
        iati_identifiers = "{}|{}".format(args.get('iati_identifier'), "|".join(
            list(map(lambda ro: "{}-{}".format(ro, args.get('iati_identifier')), args['reporting_org_code'].split("|")))))
        print("iati_identifiers are", iati_identifiers)
        print("DS URL IS {}".format(DSV1_IATI_IDENTIFIER_URL.format(iati_identifiers)))
        r = requests.get(DSV1_IATI_IDENTIFIER_URL.format(iati_identifiers))
        if r.status_code==200:
            data = clean_data(etree.fromstring(r.text))
            if len(data['results'])>0:
                return jsonify(data)

    print("DS URL IS {}".format(DSV1_TITLE_URL.format(urlencode_text(title), reporting_org_code)))
    r = requests.get(DSV1_TITLE_URL.format(title.encode("utf-8"), reporting_org_code))
    if r.status_code==200:
        data = clean_data(etree.fromstring(r.text))
        return jsonify(data)
    return jsonify({'msg': 'No results found', 'results': []})


#FIXME


@blueprint.route("/search/<iati_identifier>/", methods=["POST","GET"])
#@jwt_required()
def api_iati_search_iati_identifier(iati_identifier):
    #FIXME
    def clean_data(doc):
        def clean_activity(activity):
            title = get_narrative(activity.find("title"))
            description = get_narrative(activity.find("description"))
            return {
                'iati_identifier': activity.find("iati-identifier").text,
                'title': title,
                'description': description,
                'transactions': qimport_iati.get_transactions_summary(activity),
            }
        return {
            "activity": clean_activity(doc.xpath("//iati-activity")[0]),
        }
    r = requests.get(DSV1_IATI_IDENTIFIER_URL.format(iati_identifier))
    print("DS URL IS {}".format(DSV1_IATI_IDENTIFIER_URL.format(iati_identifier)))
    data = clean_data(etree.fromstring(r.text))
    return data


@blueprint.route("/fetch_data/<activity_id>/")
@jwt_required()
@quser.permissions_required("edit")
def api_iati_fetch_data(activity_id, methods=["POST"]):
    iati_identifier = request.args["iati_identifier"]
    #iati_document_result = qimport_iati.import_documents(activity_id, iati_identifier)
    return str(iati_document_result)
