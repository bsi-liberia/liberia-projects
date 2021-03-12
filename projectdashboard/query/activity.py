import datetime
from flask import url_for, session, flash
from flask_login import current_user
from collections import OrderedDict
from sqlalchemy import func
from sqlalchemy.orm import aliased

from six import u as unicode

from projectdashboard.lib.util import isostring_date, isostring_year
from projectdashboard.lib import codelists, util
from . import finances as qfinances
from projectdashboard.query import organisations as qorganisations
from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.query.activity_log import activity_updated


def force_earliest_latest(earliest, latest):
    if (earliest == latest) and (earliest != None):
        latest += datetime.timedelta(days=1)
        return earliest, latest
    return datetime.datetime.now().date().isoformat(), (datetime.datetime.now().date() + datetime.timedelta(days=1)).isoformat()


def get_earliest_latest_dates(force=False):
    earliest = db.session.query(func.min(models.ActivityFinances.transaction_date)).scalar()
    latest = db.session.query(func.max(models.ActivityFinances.transaction_date)).scalar()
    if (not force) or ((earliest != latest) and (earliest != None)):
        return earliest, latest
    return force_earliest_latest(earliest, latest)


def get_earliest_latest_dates_filter(filter, force=False):
    earliest = db.session.query(func.min(models.ActivityFinances.transaction_date)
        ).filter(getattr(models.Activity, filter['key']) == filter['val']
        ).join(models.Activity, models.ActivityFinances.activity
        ).scalar()
    latest = db.session.query(func.max(models.ActivityFinances.transaction_date)
        ).filter(getattr(models.Activity, filter['key']) == filter['val']
        ).join(models.Activity, models.ActivityFinances.activity
        ).scalar()
    if not force:
        return earliest, latest
    return force_earliest_latest(earliest, latest)


def activity_C_D_FSs():
    commitments_query = db.session.query(
        models.ActivityFinances.activity_id,
        func.sum(models.ActivityFinances.transaction_value).label("total_commitments")
    ).filter(models.ActivityFinances.transaction_type==u'C'
    ).group_by(models.ActivityFinances.activity_id
    ).all()
    commitments = dict(map(lambda c: (c.activity_id, c.total_commitments), commitments_query))
    disbursements_query = db.session.query(
        models.ActivityFinances.activity_id,
        func.sum(models.ActivityFinances.transaction_value).label("total_disbursements")
    ).filter(models.ActivityFinances.transaction_type==u'D'
    ).group_by(models.ActivityFinances.activity_id
    ).all()
    disbursements = dict(map(lambda d: (d.activity_id, d.total_disbursements), disbursements_query))
    forward_disbursements_query = db.session.query(
        models.ActivityForwardSpend.activity_id,
        func.sum(models.ActivityForwardSpend.value).label("total_forward_disbursements")
    ).group_by(models.ActivityForwardSpend.activity_id
    ).all()
    forward_disbursements = dict(map(lambda d: (d.activity_id, d.total_forward_disbursements), forward_disbursements_query))
    return commitments, disbursements, forward_disbursements

def filter_activities_for_permissions(query, permission_name="view"):
    permissions = current_user.permissions_dict
    if permissions.get(permission_name) == "both":
        return query
    elif permissions.get(permission_name) == "domestic":
        return query.filter(models.Activity.domestic_external == "domestic")
    elif permissions.get(permission_name) == "external":
        return query.filter(models.Activity.domestic_external == "external")
    elif permissions.get(permission_name) == "external":
        return query.filter(models.Activity.domestic_external == "external")
    elif "organisations" in permissions and permissions["organisations"]:
        def filter_permitted(organisation):
            return organisation["permission_value"] == permission_name
        permitted_organisations = list(map(lambda o: o["organisation_id"],
            filter(filter_permitted, permissions["organisations"].values())))
        return query.filter(models.Activity.reporting_org_id.in_(permitted_organisations))
    return query

def get_iati_list():
    countries_db = db.session.query(models.Activity
                    ).distinct(models.Activity.recipient_country_code
                    ).group_by(models.Activity.recipient_country_code
                    ).order_by(models.Activity.recipient_country_code).all()

    return OrderedDict(map(lambda x: (x.recipient_country_code,
          {
              "country": x.recipient_country.as_dict(),
              "urls":
                  {"1.03": url_for('iati.generate_iati_xml',
                                   version="1.03",
                                   country_code=x.recipient_country_code,
                                   _external=True),
                   "2.01": url_for('iati.generate_iati_xml',
                                   version="2.01",
                                   country_code=x.recipient_country_code,
                                   _external=True),
                  }
          }), countries_db))

def get_updates():
    the24hoursago = datetime.datetime.utcnow() - datetime.timedelta(days=1)

    created = db.session.query(models.Activity).filter(
        models.Activity.created_date > the24hoursago
    ).all()
    updated = db.session.query(models.Activity).filter(
        models.Activity.updated_date > the24hoursago
    ).all()

    created_ids = list(map(lambda x: x.id, created))

    def filterout(update):
        return update.id not in created_ids

    updated = filter(filterout, updated)
    return created, updated

def create_activity_for_test(data, user_id):
    act = models.Activity()
    act.reporting_org_id = qorganisations.get_organisation_by_name(unicode(data.get(u"Funded by"))).id
    funding_org = models.ActivityOrganisation()
    funding_org.role = 1
    funding_org.organisation_id = qorganisations.get_organisation_by_name(unicode(data.get(u"Funded by"))).id
    implementing_org = models.ActivityOrganisation()
    implementing_org.role = 4
    implementing_org.organisation_id = qorganisations.get_or_create_organisation(unicode(data.get(u"Implemented by")))
    act.organisations = [implementing_org, funding_org]
    mtef_sector = models.ActivityCodelistCode()
    mtef_sector.codelist_code_id = codelists.get_codelists_ids_by_name()['mtef-sector'][data.get(u"MTEF Sector")]
    act.classifications = [mtef_sector]
    act.title = unicode(data.get(u"Activity Title"))
    act.description = u""
    act.recipient_country_code = u"LR"
    act.domestic_external = u"external"
    act.user_id = user_id
    db.session.add(act)
    db.session.commit()
    return True

def create_activity(data):
    #FIXME check this org doesn't already exist?
    act = models.Activity()

    # Dates have to be converted to date format
    data["start_date"] = isostring_date(data["start_date"])
    data["end_date"] = isostring_date(data["end_date"])

    classifications = []
    for cl in ["sdg-goals", "mtef-sector", "aft-pillar",
        "aligned-ministry-agency", "papd-pillar"]:
        cl_id = 'classification_id_{}'.format(cl)
        cl_pct = 'classification_percentage_{}'.format(cl)
        classification = models.ActivityCodelistCode()
        classification.codelist_code_id=data[cl_id]
        classifications.append(classification)
        data.pop(cl_id)
        data.pop(cl_pct)
    act.classifications = classifications

    orgs = []
    for org_id, org_role in ((data["org_4"], 4), (data["org_1"], 1)):
        org = models.ActivityOrganisation()
        org.organisation_id = org_id
        org.role = org_role
        data.pop("org_{}".format(org_role))
        orgs.append(org)
    act.organisations = orgs

    for attr, val in data.items():
        if attr.startswith("total_"):
            if val == "":
                val = 0
        setattr(act, attr, val)
    if not "forwardspends" in data:
        act.forwardspends = qfinances.create_forward_spends(data["start_date"],
            data["end_date"])
    db.session.add(act)
    db.session.commit()

    activity_updated(act.id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "Activity",
        "target_id": act.id,
        "old_value": None,
        "value": act.as_dict()
        }
    )
    return act

def delete_activity(activity_id):
    activity = models.Activity.query.filter_by(
        id = activity_id
    ).first()
    if ((getattr(current_user, "id") == activity.user_id) or
        (getattr(current_user, "administrator"))):
       # Allow this activity to be deleted
       db.session.delete(activity)
       db.session.commit()
       return True
    activity_updated(activity.id,
        {
        "user_id": current_user.id,
        "mode": "delete",
        "target": "Activity",
        "target_id": activity.id,
        "old_value": activity.as_dict(),
        "value": None
        }
    )
    return False

def get_activity(activity_id):
    act = models.Activity.query.filter_by(
        id = activity_id
    ).first()
    return act

def list_activities():
    acts = models.Activity.query.all()
    return acts

def list_activities_by_country(recipient_country_code):
    acts = models.Activity.query.filter_by(
        recipient_country_code=recipient_country_code
    ).all()
    return acts

def getISODate(value):
    return datetime.datetime.strptime(value, '%Y-%m-%d')

def getJSONDate(value):
    return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')


def get_activities_by_reporting_org_id(reporting_org_id):
    return models.Activity.query.filter_by(reporting_org_id=reporting_org_id).all()


def list_activities_by_filters(filters, permission_name="view"):
    query = models.Activity.query.outerjoin(
                    models.ActivityFinances,
                    models.ActivityFinancesCodelistCode
                )
    codelist_names = list(codelists.get_db_codelists().keys())
    if "organisation" in codelist_names:
        codelist_names.remove("organisation")
    codelist_vals = []
    for filter_name, filter_value in filters.items():
        if filter_value == "all": continue
        if filter_name == "earliest_date":
            query = query.filter(
                models.ActivityFinances.transaction_date >= getISODate(filter_value))
        elif filter_name == "latest_date":
            query = query.filter(
                models.ActivityFinances.transaction_date <= getISODate(filter_value))
        elif filter_name in codelist_names:
            codelist_vals.append(int(filter_value))
        elif filter_name == 'implementing_org_type':
            query = query.filter(
                models.Activity.implementing_organisations.any(
                    models.Organisation._type == filter_value)
            )
        elif (filter_name == 'result_indicator_periods') and (filter_value == True):
            query = query.filter(
                models.Activity.result_indicator_periods != None
            )
        else:
            query = query.filter(
                getattr(models.Activity, filter_name)==filter_value
            )
    # This gets a bit nasty. We join multiple times to the same tables to filter by
    # multiple values. We need to use sqlalchemy.orm' aliased function for this.
    if codelist_vals:
        query = query
        for codelist_val in codelist_vals:
            this_activitycodelist_code = aliased(models.ActivityCodelistCode)
            this_codelist_code = aliased(models.CodelistCode)
            query = query.join(
                this_activitycodelist_code, models.Activity.id == this_activitycodelist_code.activity_id
            ).join(
                    this_codelist_code, this_activitycodelist_code.codelist_code_id ==  this_codelist_code.id
            )
            query = query.filter(
                    this_codelist_code.id == codelist_val
            )
    query = filter_activities_for_permissions(query, permission_name=permission_name)
    acts = query.all()
    return acts

def update_attr(data):
    if data['attr'] in ["mtef-sector", "aligned-ministry-agency", "sdg-goals"]:
        # Delete existing database entry
        old_clc = models.ActivityCodelistCode.query.filter(
            models.ActivityCodelistCode.activity_id == data['id'],
            models.CodelistCode.codelist_code == data['attr']
        ).join(
            models.CodelistCode
        ).all()
        for code in old_clc:
            db.session.delete(code)
        new_clc = models.ActivityCodelistCode()
        new_clc.activity_id = data["id"]
        new_clc.codelist_code_id = data['value']
        db.session.add(new_clc)
        db.session.commit()
        return True

    activity = models.Activity.query.filter_by(
        id = data['id']
    ).first()

    if data['attr'].endswith('date'):
        data['value'] = isostring_date(data['value'])
        if data['attr'] == "start_date":
            if data['value'].date() < activity.start_date:
                new_fs = qfinances.create_missing_forward_spends(data['value'].date(), activity.end_date, activity.id)
                activity.forwardspends += new_fs
                print("Warning: activity start date moved earlier")
            if data['value'].date() > activity.start_date:
                # FIXME: need to remove 0-valued forward spend periods
                print("Warning: activity start date moved later")
        if data['attr'] == "end_date":
            if data['value'].date() > activity.end_date:
                new_fs = qfinances.create_missing_forward_spends(activity.start_date, data['value'].date(), activity.id)
                activity.forwardspends += new_fs
                print("Warning: activity end date moved later")
            if data['value'].date() < activity.end_date:
                # FIXME: need to remove 0-valued forward spend periods
                print("Warning: activity end date moved earlier")

    if (data['attr'].startswith("total_") and data['value'] == ""):
        data['value'] = 0
    old_value = getattr(activity, data['attr'])
    setattr(activity, data['attr'], data['value'])
    activity.updated_date = datetime.datetime.utcnow()
    db.session.add(activity)
    db.session.commit()
    activity_updated(activity.id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "Activity",
        "target_id": activity.id,
        "old_value": {data['attr']: old_value},
        "value": {data['attr']: data['value']}
        }
    )
    return True



def update_activity_policy_marker(activity_id, policy_marker_code, data):
    activity_policy_marker = models.ActivityPolicyMarker.query.filter_by(
        activity_id = activity_id,
        policy_marker_code = policy_marker_code
    ).first()
    if activity_policy_marker:
        old_value = getattr(activity_policy_marker, data['attr'])
        mode = "update"
    else:
        activity_policy_marker = models.ActivityPolicyMarker()
        activity_policy_marker.activity_id = activity_id
        activity_policy_marker.policy_marker_code = policy_marker_code
        old_value = {}
        mode = "add"
    setattr(activity_policy_marker, data['attr'], data['value'])
    db.session.add(activity_policy_marker)
    db.session.commit()
    activity_updated(activity_id,
        {
        "user_id": current_user.id,
        "mode": mode,
        "target": "ActivityPolicyMarker",
        "target_id": activity_policy_marker.id,
        "old_value": old_value,
        "value": {data['attr']: data['value']}
        }
    )
    return True



def update_activity_codelist(activitycodelistcode_id, data):
    activity_codelist = models.ActivityCodelistCode.query.filter_by(
        id = activitycodelistcode_id
    ).first()
    if not activity_codelist: return False
    old_value = getattr(activity_codelist, data['attr'])
    setattr(activity_codelist, data['attr'], data['value'])
    db.session.add(activity_codelist)
    db.session.commit()
    activity_updated(activity_codelist.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityCodelistCode",
        "target_id": activity_codelist.id,
        "old_value": {data['attr']: old_value},
        "value": {data['attr']: data['value']}
        }
    )
    return True


def save_period_data(indicator_id, periods_data):
    existing_periods = models.ActivityResultIndicator.query.get(indicator_id).periods
    existing_period_ids = list(map(lambda p: p.id, existing_periods))
    new_period_ids = list(map(lambda p: p.get("id"), periods_data))
    # Delete periods that no longer appear
    periods_to_delete = filter(lambda r: r not in new_period_ids, existing_period_ids)
    [delete_result_data({'result_type': "ActivityResultIndicatorPeriod", "id": period}) for period in periods_to_delete]
    for period in periods_data:
        if not "id" in period:
            # Create a new period
            new_period = add_indicator_period(period, indicator_id)
        else:
            # Update period
            for k, v in period.items():
                if k in ['open', 'percent_complete', 'percent_complete_category']: continue
                update_indicator_period_attr({'id': period['id'], 'attr': k, 'value': v})

def save_indicator_data(result_id, data):
    existing_indicators = models.ActivityResult.query.get(result_id).indicators
    if not "indicator_id" in data:
        if len(existing_indicators) > 0:
            for existing_indicator in existing_indicators:
                delete_result_data({"result_type": "ActivityResultIndicator", "id": existing_indicator.id})
        else:
            # Indicator is new
            add_indicator(data, result_id)
    elif (len(existing_indicators) == 1) and (data.get("indicator_id") == existing_indicators[0].id):
        # Indicator exists
        for k in ['indicator_title', 'baseline_year', 'baseline_value', 'measurement_unit_type', 'measurement_type']:
            indicator = update_indicator_attr({'id': result_id, 'attr': k, 'value': data.get(k)})
        save_period_data(indicator.id, data.get('periods', []))


def save_results_data_entry(activity_id, results_data, save_type):
    activity = models.Activity.query.get(activity_id)
    existing_results = activity.results
    existing_result_ids = set(map(lambda r: r.id, existing_results))
    new_result_ids = set(map(lambda r: r.get("id"), results_data))
    assert new_result_ids == existing_result_ids
    for result in results_data:
        existing_result = models.ActivityResult.query.get(result["id"])
        existing_period_ids = set(map(lambda p: p.id, existing_result.indicator_periods))
        new_period_ids = set(map(lambda p: p["id"], result["periods"]))
        assert existing_period_ids == new_period_ids
        for period in result["periods"]:
            existing_period = models.ActivityResultIndicatorPeriod.query.get(period["id"])
            if (existing_period.open == False) or (existing_period.status == 4): continue
            update_indicator_period_attr(
                {'id': period['id'],
                'attr': 'actual_value',
                'value': period['actual_value']}
            )
            if ((save_type == "submitAll") or
                ((save_type == "submitSelected") and (period['status'] == '4'))):
                update_indicator_period_attr(
                    {'id': period['id'],
                    'attr': 'status',
                    'value': 4}
                )
            else:
                update_indicator_period_attr(
                    {'id': period['id'],
                    'attr': 'status',
                    'value': 3}
                )

    return True


def save_results_data(activity_id, results_data):
    activity = models.Activity.query.get(activity_id)
    existing_results = activity.results
    existing_result_ids = list(map(lambda r: r.id, existing_results))
    new_result_ids = list(map(lambda r: r.get("id"), results_data))
    # Delete results that no longer appear
    results_to_delete = filter(lambda r: r not in new_result_ids, existing_result_ids)
    [delete_result_data({'result_type': "ActivityResult", "id": result}) for result in results_to_delete]

    for result in results_data:
        if not "id" in result:
            result_to_add = result
            result_to_add['result_type'] = {'Output': 1, 'Outcome': 2, 'Impact': 3}[result['result_type']]
            result_to_add["indicators"] = [result] # They use different names so this is OK
            new_result = add_result(result_to_add, activity_id)
        else:
            existing_result = update_result_attr({
                    'id': result['id'],
                    'attr': 'result_title',
                    'value': result['result_title']
                })
            existing_result = update_result_attr({
                    'id': result['id'],
                    'attr': 'result_type',
                    'value': {'Output': 1, 'Outcome': 2, 'Impact': 3}[result['result_type']]
                })
            save_indicator_data(existing_result.id, result)
    return True

def update_result_attr(data):
    result = models.ActivityResult.query.filter_by(
        id = data['id']
    ).first()
    oldresult = result.as_dict()
    setattr(result, data['attr'], data['value'])
    db.session.add(result)
    db.session.commit()
    activity_updated(result.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityResult",
        "target_id": result.id,
        "old_value": oldresult,
        "value": result.as_dict()
        }
    )
    return result

def update_indicator_attr(data):
    indicator = models.ActivityResultIndicator.query.filter_by(
        id = data['id']
    ).first()
    oldindicator = indicator.as_dict()
    if (data['attr'].endswith("year")) and not (data['value'] in (None, '')):
        data['value'] = isostring_year(str(data['value']))
    setattr(indicator, data['attr'], data['value'])
    db.session.add(indicator)
    db.session.commit()
    activity_updated(indicator.result.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityResultIndicator",
        "target_id": indicator.id,
        "old_value": oldindicator,
        "value": indicator.as_dict()
        }
    )
    return indicator

def update_indicator_period_attr(data):
    period = models.ActivityResultIndicatorPeriod.query.filter_by(
        id = data['id']
    ).first()
    oldperiod = period.as_dict()
    if data['attr'].startswith("period_"):
        data['value'] = isostring_date(data['value'])
    if hasattr(period, data['attr']):
        setattr(period, data['attr'], data['value'])
    db.session.add(period)
    db.session.commit()
    activity_updated(period.result_indicator.result.activity_id,
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityResultIndicatorPeriod",
        "target_id": period.id,
        "old_value": oldperiod,
        "value": period.as_dict()
        }
    )
    return period

def add_indicator_period(data, indicator_id, commit=True):
    p = models.ActivityResultIndicatorPeriod()
    p.period_start = isostring_date(data.get("period_start"))
    p.period_end = isostring_date(data.get("period_end"))
    p.target_value = data.get("target_value")
    p.target_comment = data.get("target_comment")
    p.actual_value = data.get("actual_value")
    p.actual_comment = data.get("actual_comment")
    p.indicator_id = indicator_id
    db.session.add(p)
    db.session.commit()
    activity_updated(p.result_indicator.result.activity_id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "ActivityResultIndicatorPeriod",
        "target_id": p.id,
        "old_value": None,
        "value": p.as_dict()
        }
    )
    return p

def add_indicator(data, result_id, commit=True):
    i = models.ActivityResultIndicator()
    i.indicator_title = data.get('indicator_title')
    i.indicator_description = data.get('indicator_description')
    if data.get("baseline_year"):
        i.baseline_year = isostring_year(data.get('baseline_year'))
    i.baseline_value = data.get('baseline_value')
    i.baseline_description = data.get('baseline_description')
    i.measurement_type = data.get('measurement_type')
    i.measurement_unit_type = data.get('measurement_unit_type')
    i.result_id = result_id
    db.session.add(i)
    db.session.commit()
    if data.get("periods"):
        [add_indicator_period(period, i.id, False) for
                              period in data['periods']]
    activity_updated(i.result.activity_id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "ActivityResultIndicator",
        "target_id": i.id,
        "old_value": None,
        "value": i.as_dict()
        }
    )
    return i

def add_result(data, activity_id, organisation_slug=None, commit=True):
    r = models.ActivityResult()
    r.result_title = data.get('result_title')
    r.result_description = data.get('result_description')
    r.result_type = data.get('result_type')
    r.activity_id = activity_id
    db.session.add(r)
    db.session.commit()
    if data.get("indicators"):
        [add_indicator(indicator, r.id, False) for
                       indicator in data['indicators']]
    activity_updated(activity_id,
        {
        "user_id": current_user.id,
        "mode": "add",
        "target": "ActivityResult",
        "target_id": r.id,
        "old_value": None,
        "value": r.as_dict()
        }
    )
    return r

def add_results_data(results, activity_id, organisation_slug):
    [add_result(result, activity_id, organisation_slug,
                False) for result in results]

def add_result_data(activity_id, data):
    if data['type'] == "ActivityResult":
        r = models.ActivityResult()
        r.activity_id = activity_id
    elif data['type'] == "ActivityResultIndicator":
        r = models.ActivityResultIndicator()
    elif data['type'] == "ActivityResultIndicatorPeriod":
        r = models.ActivityResultIndicatorPeriod()

    for k, v in data.items():
        if k.startswith('period'):
            v = isostring_date(v)
        if k.endswith('year'):
            v = isostring_year(v)
        setattr(r, k, v)
    db.session.add(r)
    db.session.commit()
    return r

def delete_result_data(data):
    if data['result_type'] == "ActivityResult":
        r = models.ActivityResult.query.filter_by(
            id = data['id']
        ).first()
        activity_id = r.activity_id
    elif data['result_type'] == "ActivityResultIndicator":
        r = models.ActivityResultIndicator.query.filter_by(
            id = data['id']
        ).first()
        activity_id = r.result.activity_id
    elif data['result_type'] == "ActivityResultIndicatorPeriod":
        r = models.ActivityResultIndicatorPeriod.query.filter_by(
            id = data['id']
        ).first()
        activity_id = r.result_indicator.result.activity_id

    activity_updated(activity_id,
        {
        "user_id": current_user.id,
        "mode": "delete",
        "target": data["result_type"],
        "target_id": r.id,
        "old_value": r.as_dict(),
        "value": None
        }
    )
    db.session.delete(r)
    db.session.commit()
