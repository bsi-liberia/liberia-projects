from maediprojects import app, db, models
import datetime
from maediprojects.query import activity as qactivity
from lxml import etree as et
from maediprojects.lib.codelist_helpers import codelists 
from maediprojects.lib.codelists import get_codelists_lookups

def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")
    
def date_isostring(value):
    # Returns a string of format YYYY-MM-DD from a date object
    return value.isoformat()
    
def current_datetime():
    return datetime.datetime.now().replace(
            microsecond=0).isoformat()
    
def actual_or_planned(value):
    date = isostring_date(value)
    current_datetime = datetime.datetime.now()
    if date > current_datetime:
        return "actual"
    return "planned"

def el_with_narrative(element_name, narrative):
    el = et.Element(element_name)
    el_nar = et.Element("narrative")
    el.append(el_nar)
    el_nar.text = narrative
    return el

def el_with_text(element_name, text):
    el = et.Element(element_name)
    el.text = text
    return el

# Generate activity date: actual if in past, otherwise planned
def el_date_103(start_end, iso_date):
    adt = codelists("1.03")["ActivityDateType"]
    
    actual_planned = actual_or_planned(iso_date)
    date_type = adt[start_end][actual_or_planned(iso_date)]
    
    el = et.Element('activity-date')
    el.set("type", date_type)
    el.set("iso-date", iso_date)
    return el

# Generate activity date: actual if in past, otherwise planned
def el_date(start_end, iso_date):
    adt = codelists("ActivityDateType")
    
    actual_planned = actual_or_planned(iso_date)
    date_type = adt[start_end][actual_or_planned(iso_date)]
    
    el = et.Element('activity-date')
    el.set("type", date_type)
    el.set("iso-date", iso_date)
    return el
    
def el_org_103(role, o_name, o_ref=None, o_type=None):
    if role == "reporting":
        el = et.Element("reporting-org")
    else:
        r = codelists("OrganisationRole")
        el = et.Element("participating-org")
        el.set("role", role)
    if o_ref: el.set("ref", o_ref)
    if o_type: el.set("type", o_type)
    el.text = o_name
    return el
    
def el_org(role, o_name, o_ref=None, o_type=None):
    if role == "reporting":
        el = et.Element("reporting-org")
    else:
        r = codelists("OrganisationRole")
        el = et.Element("participating-org")
        el.set("role", r[role])
    if o_ref: el.set("ref", o_ref)
    if o_type: el.set("type", o_type)
    el_nar = et.Element("narrative")
    el.append(el_nar)
    el_nar.text = o_name
    return el
    
def el_iati_identifier(activity, o_ref):
    el = et.Element("iati-identifier")
    a_code = activity.code
    el.text = "%s-%s" % (o_ref, a_code)
    return el

def el_with_code_103(element_name, code, text, vocabulary=None):
    el = et.Element(element_name)
    el.set("code", code)
    if vocabulary:
        el.set("vocabulary", vocabulary)
    el.text = text
    return el

def el_with_code(element_name, code, vocabulary=None):
    el = et.Element(element_name)
    el.set("code", code)
    if vocabulary:
        el.set("vocabulary", vocabulary)
    return el
    
def el_location(location):
    el = et.Element("location")
    
    location_reach = et.Element("location-reach")
    el.append(location_reach)
    location_reach.set("code", "1")
    
    location_id = et.Element("location-id")
    el.append(location_id)
    location_id.set("vocabulary", "G1")
    location_id.set("code", str(location.locations.geonames_id))

    name = et.Element("name")
    el.append(name)
    name_narr = et.Element("narrative")
    name.append(name_narr)
    name_narr.text = location.locations.name
    
    feature_adm = {"ADM1": "1", "ADM2": "2"}
    
    if ((feature_adm[location.locations.feature_code] == "2") and 
        (location.locations.admin1_code != "")):
        administrative = et.Element("administrative")
        el.append(administrative)
        administrative.set("vocabulary", "G1")
        administrative.set("level", "1")
        administrative.set("code", str(location.locations.admin1_code))
    
    administrative = et.Element("administrative")
    el.append(administrative)
    administrative.set("vocabulary", "G1")
    administrative.set("level", feature_adm[location.locations.feature_code])
    administrative.set("code", str(location.locations.geonames_id))

    point = et.Element("point")
    el.append(point)
    point.set("srsName", "http://www.opengis.net/def/crs/EPSG/0/4326")
    point_pos = et.Element("pos")
    point.append(point_pos)
    point_pos.text = "%s %s" % (location.locations.latitude, 
                                location.locations.longitude)

    location_class = et.Element("location-class")
    el.append(location_class)
    location_class.set("code", "1")

    feature_designation = et.Element("feature-designation")
    el.append(feature_designation)
    feature_designation.set("code", "ADMD")

    return el
    
def el_location_103(location):
    el = et.Element("location")

    location_type = et.Element("location-type")
    el.append(location_type)
    location_type.set("code", "ADMD")

    feature_precision = {"ADM1": "4", "ADM2": "3"}

    coordinates = et.Element("coordinates")
    el.append(coordinates)
    coordinates.set("latitude", location.locations.latitude)
    coordinates.set("longitude", location.locations.longitude)
    coordinates.set("precision", feature_precision[location.locations.feature_code])

    name = et.Element("name")
    el.append(name)
    name.text = location.locations.name

    gazetteer_entry = et.Element("gazetteer-entry")
    el.append(gazetteer_entry)
    gazetteer_entry.set("gazetteer-ref", "GEO")
    gazetteer_entry.text = str(location.locations.geonames_id)

    return el
    
def el_with_attrib(element_name, attrib, attrib_value):
    el = et.Element(element_name)
    el.set(attrib, attrib_value)
    return el
    
def el_contact_info(organisation):
    ec = et.Element("contact-info")
    ec.append(el_with_narrative("organisation",
              organisation["organisation_name"]))
    ec.append(el_with_narrative("person-name",
              organisation["organisation_contact_name"]))
    ec.append(el_with_text("telephone",
              organisation["organisation_contact_phone"]))
    ec.append(el_with_text("email",
              organisation["organisation_contact_email"]))
    ec.append(el_with_text("website",
              organisation["organisation_contact_website"]))
    ec.append(el_with_narrative("mailing-address",
              organisation["organisation_contact_address"]))
    return ec
    
def build_transaction_103(transaction):
    transaction_id = str(transaction["id"])
    transaction_date = transaction["transaction_date"].isoformat()
    transaction_value = transaction["transaction_value"]
    transaction_description = transaction["transaction_description"]
    
    trt = transaction["transaction_type"]
    if trt == "D": trtval = "D"
    if trt == "C": trtval = "C"
    tt = codelists("1.03")["TransactionType"]
    transaction_type_name = tt[trtval]
    
    t = et.Element("transaction")
    t.set("ref", transaction_id)
    
    t.append(el_with_code_103("transaction-type", 
                              transaction["transaction_type"],
                              transaction_type_name))
    
    tdate = et.Element("transaction-date")
    t.append(tdate)
    tdate.set("iso-date", transaction_date)
    
    tvalue = et.Element("value")
    t.append(tvalue)
    tvalue.text = unicode(transaction_value)
    tvalue.set("value-date", transaction_date)
    
    if transaction_description:
        t.append(el_with_text("description", transaction_description))
    
    return t
    
def build_transaction(transaction):
    transaction_id = str(transaction["id"])
    transaction_date = transaction["transaction_date"].isoformat()
    transaction_value = transaction["transaction_value"]
    transaction_description = transaction["transaction_description"]
    
    trt = transaction["transaction_type"]
    if trt == "D": trtval = "D"
    if trt == "C": trtval = "C"
    tt = codelists("TransactionType")
    transaction_type = tt[trtval]
    
    t = et.Element("transaction")
    t.set("ref", transaction_id)
    
    t.append(el_with_code("transaction-type", transaction_type))
    
    tdate = et.Element("transaction-date")
    t.append(tdate)
    tdate.set("iso-date", transaction_date)
    
    tvalue = et.Element("value")
    t.append(tvalue)
    tvalue.text = unicode(transaction_value)
    tvalue.set("value-date", transaction_date)
    
    if transaction_description:
        t.append(el_with_narrative("description", transaction_description))
    
    return t

def valid_transaction(transaction):
    return (transaction.transaction_date and transaction.transaction_value > 0)
    
def build_activity_103(doc, activity):
    db_activity = activity
    
    cl_lookups = get_codelists_lookups()
    
    ia = et.Element("iati-activity")
    doc.append(ia)

    ia.set("last-updated-datetime", current_datetime())
    #FIXME: put default currency in organisation settings
    ia.set("default-currency", app.config["ORGANISATION"]["default_currency"])
    
    o_name = app.config["ORGANISATION"]["organisation_name"]
    o_ref = app.config["ORGANISATION"]["organisation_ref"]
    o_type = app.config["ORGANISATION"]["organisation_type"]
    
    # IATI Identifier
    ia.append(el_iati_identifier(activity, o_ref))
    
    # Reporting org
    ia.append(el_org_103("reporting", o_name, o_ref, o_type))
    
    # Title, Description
    ia.append(el_with_text("title", activity.title))
    ia.append(el_with_text("description", activity.description))
    
    # Participating orgs
    ia.append(el_org_103("Funding", app.config["ORGANISATION"]["organisation_name"], 
                                app.config["ORGANISATION"]["organisation_ref"], 
                                app.config["ORGANISATION"]["organisation_type"]))
    ia.append(el_org_103("Implementing", activity.implementing_org))
    ia.append(el_org_103("Extending", activity.executing_org_name.name, 
                            activity.executing_org_name.code, "10"))
    
    ia.append(el_with_code("activity-status", activity.activity_status))
    
    # Activity dates
    if activity.start_date:
        ia.append(el_date_103("start", activity.start_date.isoformat()))
    if activity.end_date:
        ia.append(el_date_103("end", activity.end_date.isoformat()))
    
    # Contact info
    #ia.append(el_contact_info(app.config["ORGANISATION"]))
    
    # Geography
    ia.append(el_with_code_103("recipient-country", 
                  activity.recipient_country_code,
                  cl_lookups["Country"][activity.recipient_country_code],
                  ))
    
    for location in activity.locations:
        ia.append(el_location_103(location))
    
    # Classifications
    ia.append(el_with_code_103("sector", 
                               activity.dac_sector, 
                               cl_lookups["Sector"][activity.dac_sector],
                               "DAC"))
    ia.append(el_with_code_103("collaboration-type", 
                               activity.collaboration_type,
                               cl_lookups["CollaborationType"][activity.collaboration_type]
                               ))
    ia.append(el_with_code_103("default-finance-type",
                               activity.finance_type,
                               cl_lookups["FinanceType"][activity.finance_type]
                               ))
    ia.append(el_with_code_103("default-flow-type",
                               activity.flow_type,
                               cl_lookups["FlowType"][activity.flow_type]))
    ia.append(el_with_code_103("default-aid-type", 
                               activity.aid_type,
                               cl_lookups["AidType"][activity.aid_type]))
    ia.append(el_with_code_103("default-tied-status", 
                               activity.tied_status,
                               cl_lookups["TiedStatus"][activity.tied_status]))

    # Transactions
    activity_commitments = filter(valid_transaction, activity.commitments)
    activity_disbursements = filter(valid_transaction, activity.disbursements)

    # Output commitments
    for transaction in activity_commitments:
        ia.append(build_transaction_103(transaction.as_dict()))

    if ((len(activity_commitments) == 0) and 
        activity.start_date and activity.total_commitments):
        transaction = { "id": "%s-C" % activity.id,
                        "transaction_date": activity.start_date,
                        "transaction_value": activity.total_commitments,
                        "transaction_description": "Total commitments",
                        "transaction_type": "C"
                        }
        ia.append(build_transaction_103(transaction))

    # Output disbursements
    for transaction in activity_disbursements:
        ia.append(build_transaction_103(transaction.as_dict()))

    if ((len(activity_disbursements) == 0) and 
        activity.total_disbursements):
        transaction = { "id": "%s-D" % activity.id,
                        "transaction_date": datetime.datetime.utcnow().date(),
                        "transaction_value": activity.total_disbursements,
                        "transaction_description": "Total disbursements",
                        "transaction_type": "D"
                        }
        ia.append(build_transaction_103(transaction))

    return doc
    
def build_activity(doc, activity):
    db_activity = activity
    
    ia = et.Element("iati-activity")
    doc.append(ia)

    ia.set("last-updated-datetime", current_datetime())
    #FIXME: put default currency in organisation settings
    ia.set("default-currency", app.config["ORGANISATION"]["default_currency"])
    
    o_name = app.config["ORGANISATION"]["organisation_name"]
    o_ref = app.config["ORGANISATION"]["organisation_ref"]
    o_type = app.config["ORGANISATION"]["organisation_type"]
    
    # IATI Identifier
    ia.append(el_iati_identifier(activity, o_ref))
    
    # Reporting org
    ia.append(el_org("reporting", o_name, o_ref, o_type))
    
    # Title, Description
    ia.append(el_with_narrative("title", activity.title))
    ia.append(el_with_narrative("description", activity.description))
    
    # Participating orgs
    ia.append(el_org("Funding", app.config["ORGANISATION"]["organisation_name"], 
                                app.config["ORGANISATION"]["organisation_ref"], 
                                app.config["ORGANISATION"]["organisation_type"]))
    ia.append(el_org("Implementing", activity.implementing_org))
    ia.append(el_org("Extending", activity.executing_org_name.name, 
                            activity.executing_org_name.code, o_type))
    
    ia.append(el_with_code("activity-status", activity.activity_status))
    
    # Activity dates
    if activity.start_date:
        ia.append(el_date("start", activity.start_date.isoformat()))
    if activity.end_date:
        ia.append(el_date("end", activity.end_date.isoformat()))
    
    # Contact info
    #ia.append(el_contact_info(app.config["ORGANISATION"]))
    
    # Geography
    ia.append(el_with_code("recipient-country", 
                  activity.recipient_country_code))

    for location in activity.locations:
        ia.append(el_location(location))

    # Classifications
    ia.append(el_with_code("sector", activity.dac_sector, "1"))

    ia.append(el_with_code("collaboration-type", activity.collaboration_type))
    ia.append(el_with_code("default-flow-type", activity.flow_type))
    ia.append(el_with_code("default-finance-type", activity.finance_type))
    ia.append(el_with_code("default-aid-type", activity.aid_type))
    ia.append(el_with_code("default-tied-status", activity.tied_status))

    # Transactions
    activity_commitments = filter(valid_transaction, activity.commitments)
    activity_disbursements = filter(valid_transaction, activity.disbursements)

    # Output commitments
    for transaction in activity_commitments:
        ia.append(build_transaction(transaction.as_dict()))
        
    if ((len(activity_commitments) == 0) and 
        activity.start_date and activity.total_commitments):
        transaction = { "id": "%s-C" % activity.id,
                        "transaction_date": activity.start_date,
                        "transaction_value": activity.total_commitments,
                        "transaction_description": "Total commitments",
                        "transaction_type": "C"
                        }
        ia.append(build_transaction(transaction))

    # Output disbursemenets
    for transaction in activity_disbursements:
        ia.append(build_transaction(transaction.as_dict()))

    if ((len(activity_disbursements) == 0) and 
        activity.total_disbursements):
        transaction = { "id": "%s-D" % activity.id,
                        "transaction_date": datetime.datetime.utcnow().date(),
                        "transaction_value": activity.total_disbursements,
                        "transaction_description": "Total disbursements",
                        "transaction_type": "D"
                        }
        ia.append(build_transaction(transaction))

    return doc

# Process activities for 1.03
def generate_iati_activity_data_103(activities):
    doc = et.Element('iati-activities')
    doc.set("version", "1.03")
    doc.set("generated-datetime", current_datetime())
    for activity in activities:
        doc = build_activity_103(doc, activity)
    doc = et.ElementTree(doc)
    return doc

# Process activities for 2.01
def generate_iati_activity_data_201(activities):
    doc = et.Element('iati-activities')
    doc.set("version", "2.01")
    doc.set("generated-datetime", current_datetime())
    for activity in activities:
        doc = build_activity(doc, activity)
    doc = et.ElementTree(doc)
    return doc
    
def el_with_isodate(element_name, iso_date):
    el = et.Element(element_name)
    el.set("iso-date", date_isostring(iso_date))
    return el

def el_total_budget(budget):
    el_b = et.Element("total-budget")
    el_b.append(el_with_isodate("period-start", budget.start_date))
    el_b.append(el_with_isodate("period-end", budget.end_date))
    el_val = el_with_text("value", str(budget.value))
    el_val.set("value-date", date_isostring(budget.start_date))
    el_b.append(el_val)    
    return el_b
    
def el_org_doc(document):
    el_d = et.Element("document-link")
    el_d.set("url", document.url)
    el_d.set("format", document.format)
    el_d.append(el_with_narrative("title", document.title))
    el_d.append(el_with_attrib("category", "code", document.category))
    return el_d
    
def build_organisation(doc, organisation):
    o_name = organisation.organisation_name
    o_ref = organisation.organisation_ref
    o_type = organisation.organisation_type
    o_currency = organisation.organisation_default_currency
    
    org = el_with_attrib("iati-organisation", "last-updated-datetime",
                         current_datetime())
    doc.append(org)
    org.set("default-currency", o_currency)
    org.append(el_with_text("organisation-identifier",
                            o_ref))
    org.append(el_with_narrative("name", o_name))

    # Reporting org
    org.append(el_org("reporting", o_name, o_ref, o_type))
    
    # Total budgets
    #for budget in organisation.budgets:
    #    org.append(el_total_budget(budget))
        
    # Documents
    for document in organisation.documents:
        org.append(el_org_doc(document))
    return doc
    
# ORGANISATION FILE
def generate_iati_organisation_data(organisation_slug):
    organisation = siorganisation.get_org(organisation_slug)
    doc = et.Element('iati-organisations')
    doc.set("version", "2.01")
    doc.set("generated-datetime", current_datetime())
    doc = build_organisation(doc, organisation)
    doc = et.ElementTree(doc)
    return doc

def generate_103(country_code):
    activities = qactivity.list_activities_by_country(country_code)
    return et.tostring(generate_iati_activity_data_103(activities))

def generate_201(country_code):
    activities = qactivity.list_activities_by_country(country_code)
    return et.tostring(generate_iati_activity_data_201(activities))