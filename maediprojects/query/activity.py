from maediprojects import db, models
import datetime
from flask.ext.login import current_user

def isostring_date(value):
    # Returns a date object from a string of format YYYY-MM-DD
    return datetime.datetime.strptime(value, "%Y-%m-%d")

def isostring_year(value):
    # Returns a date object from a string of format YYYY
    return datetime.datetime.strptime(value, "%Y")

def create_activity(data):
    #FIXME check this org doesn't already exist?
    act = models.Activity()

    # Dates have to be converted to date format, then removed from the
    # dict so they don't attempt to be re-set below...
    act.start_date = isostring_date(data.pop("start_date"))
    act.end_date = isostring_date(data.pop("end_date"))
    
    for attr, val in data.items():
        setattr(act, attr, val)
    db.session.add(act)
    db.session.commit()
    return act

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
    if(hasattr(current_user, "id") and (not current_user.administrator)):
        return models.Activity.query.filter_by(
        user_id = current_user.id
        ).all()
    return models.Activity.query.all()

def list_activities_by_country(recipient_country_code):
    acts = models.Activity.query.filter_by(
        recipient_country_code=recipient_country_code
    ).all()
    return acts

def update_attr(data):
    activity = models.Activity.query.filter_by(
        id = data['id']
    ).first()
    if data['attr'].endswith('date'):
        data['value'] = isostring_date(data['value'])
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