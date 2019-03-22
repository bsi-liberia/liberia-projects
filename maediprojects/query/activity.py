import datetime
from flask import url_for, session, flash
from flask_login import current_user
from collections import OrderedDict
from sqlalchemy import func
from sqlalchemy.orm import aliased

from maediprojects.lib.util import isostring_date, isostring_year
from maediprojects.lib import codelists, util
from maediprojects.query import finances as qfinances
from maediprojects import models
from maediprojects.extensions import db


def get_earliest_latest_dates():
    earliest = db.session.query(func.min(models.ActivityFinances.transaction_date)).scalar()
    latest = db.session.query(func.max(models.ActivityFinances.transaction_date)).scalar()
    return earliest, latest

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

def filter_activities_for_permissions(query):
    permissions = session.get("permissions", {})
    if permissions.get("domestic_external") == "both":
        return query
    elif permissions.get("domestic_external") == "domestic":
        return query.filter(models.Activity.domestic_external == "domestic")
    elif permissions.get("domestic_external") == "external":
        return query.filter(models.Activity.domestic_external == "external")
    elif permissions.get("domestic_external") == "external":
        return query.filter(models.Activity.domestic_external == "external")
    elif "organisations" in permissions and permissions["organisations"]:
        return query.filter(models.Activity.reporting_org_id.in_(permissions["organisations"].keys()))
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
                  {"1.03": url_for('api.generate_iati_xml',
                                   version="1.03",
                                   country_code=x.recipient_country_code,
                                   _external=True),
                   "2.01": url_for('api.generate_iati_xml',
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

def activity_add_log(activity_id, user_id, mode, target, old_value, value):
    activity_log = models.ActivityLog()
    activity_log.activity_id = activity_id
    activity_log.user_id = user_id
    activity_log.mode = mode
    activity_log.target = target
    activity_log.old_value = old_value
    activity_log.value = value
    db.session.add(activity_log)
    db.session.commit()
    return activity_log

def activity_updated(activity_id, update_data=False):
    activity = models.Activity.query.filter_by(id=activity_id).first()
    if not activity:
        flash("Could not update last updated date for activity ID {}: activity not found".format(
            activity_id), "danger")
        return False
    activity.updated_date = datetime.datetime.utcnow()
    db.session.add(activity)
    db.session.commit()
    print update_data
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
    return False

def get_activity(activity_id):
    act = models.Activity.query.filter_by(
        id = activity_id
    ).first()
    return act

def list_activities():
    acts = models.Activity.query.all()
    return acts

def get_stats(current_user):
    activities = list_activities_user(current_user)
    return {
        "count": len(activities)
    }

def list_activities_user(current_user):
    # FIXME Simplify this by removing this function -- all requests
    # for activities should be passed through filter..._for_permissions
    if(hasattr(current_user, "id") and (not current_user.administrator)):
        query = models.Activity.query.filter_by(
        user_id = current_user.id
        )
    else:
        query = models.Activity.query
    query = filter_activities_for_permissions(query)
    return query.all()

def list_activities_by_country(recipient_country_code):
    acts = models.Activity.query.filter_by(
        recipient_country_code=recipient_country_code
    ).all()
    return acts

def getJSONDate(value):
    return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')

def list_activities_by_filters(filters):
    query = models.Activity.query.outerjoin(
                    models.ActivityFinances,
                    models.ActivityFinancesCodelistCode
                )
    codelist_names = codelists.get_db_codelists().keys()
    codelist_names.remove("organisation")
    codelist_vals = []
    for filter_name, filter_value in filters.items():
        if filter_value == "all": continue
        if filter_name == "earliest_date":
            query = query.filter(
                models.ActivityFinances.transaction_date > getJSONDate(filter_value))
        elif filter_name == "latest_date":
            query = query.filter(
                models.ActivityFinances.transaction_date < getJSONDate(filter_value))
        elif filter_name in codelist_names:
            codelist_vals.append(int(filter_value))
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
    query = filter_activities_for_permissions(query)
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
    setattr(activity, data['attr'], data['value'])
    activity.updated_date = datetime.datetime.utcnow()
    db.session.add(activity)
    db.session.commit()
    return True

def update_result_attr(data):
    result = models.ActivityResult.query.filter_by(
        id = data['id']
    ).first()
    setattr(result, data['attr'], data['value'])
    db.session.add(result)
    db.session.commit()
    return result

def update_indicator_attr(data):
    indicator = models.ActivityResultIndicator.query.filter_by(
        id = data['id']
    ).first()
    if data['attr'].endswith("year"):
        data['value'] = isostring_year(data['value'])
    setattr(indicator, data['attr'], data['value'])
    db.session.add(indicator)
    db.session.commit()
    return indicator

def update_indicator_period_attr(data):
    period = models.ActivityResultIndicatorPeriod.query.filter_by(
        id = data['id']
    ).first()
    if data['attr'].startswith("period_"):
        data['value'] = isostring_date(data['value'])
    setattr(period, data['attr'], data['value'])
    db.session.add(period)
    db.session.commit()
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
    return p

def add_indicator(data, result_id, commit=True):
    print "indicator"
    i = models.ActivityResultIndicator()
    i.indicator_title = data.get('indicator_title')
    i.indicator_description = data.get('indicator_description')
    i.baseline_year = isostring_year(data.get('baseline_year'))
    i.baseline_description = data.get('baseline_description')
    i.result_id = result_id
    db.session.add(i)
    db.session.commit()
    if data.get("periods"):
        [add_indicator_period(period, i.id, False) for
                              period in data['periods']]
    return i

def add_result(data, activity_id, organisation_slug, commit=True):
    r = models.ActivityResult()
    r.result_title = data.get('result_title')
    r.result_description = data.get('result_description')
    r.result_type = data.get('result_type')
    r.activity_id = activity_id
    r.organisation_slug = organisation_slug
    db.session.add(r)
    db.session.commit()
    if data.get("indicators"):
        [add_indicator(indicator, r.id, False) for
                       indicator in data['indicators']]
    return r

def add_results_data(results, activity_id, organisation_slug):
    [add_result(result, activity_id, organisation_slug,
                False) for result in results]

def add_result_data(activity_id, data):
    if data['type'] == "result":
        r = models.ActivityResult()
        r.activity_id = activity_id
    elif data['type'] == "indicator":
        r = models.ActivityResultIndicator()
    elif data['type'] == "period":
        r = models.ActivityResultIndicatorPeriod()

    for k, v in data.items():
        if k.startswith('period'):
            v = isostring_date(v)
        if k.endswith('year'):
            v = isostring_year(v)
        setattr(r, k, v)
    print "Adding"
    db.session.add(r)
    db.session.commit()
    return r

def delete_result_data(data):
    if data['result_type'] == "result":
        r = models.ActivityResult.query.filter_by(
            id = data['id']
        ).first()
    elif data['result_type'] == "indicator":
        r = models.ActivityResultIndicator.query.filter_by(
            id = data['id']
        ).first()
    elif data['result_type'] == "period":
        r = models.ActivityResultIndicatorPeriod.query.filter_by(
            id = data['id']
        ).first()
    db.session.delete(r)
    db.session.commit()