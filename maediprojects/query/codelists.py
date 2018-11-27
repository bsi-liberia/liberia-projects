from flask.ext.login import current_user
from maediprojects import db, models
import activity as qactivity
import datetime
import normality

def update_activity_codelist(activitycodelistcode_id, data):
    activity_codelist = models.ActivityCodelistCode.query.filter_by(
        id = activitycodelistcode_id
    ).first()
    if not activity_codelist: return False
    old_value = getattr(activity_codelist, data['attr'])
    setattr(activity_codelist, data['attr'], data['value'])
    db.session.add(activity_codelist)
    db.session.commit()
    qactivity.activity_updated(activity_codelist.activity_id, 
        {
        "user_id": current_user.id,
        "mode": "update",
        "target": "ActivityCodelistCode",
        "target_id": activity_codelist.id,
        "old_value": {data['attr']: old_value},
        "value": {data['attr']: data['value']}
        }
    )
    print data
    return True

def get_code_by_name(codelist, name):
    code = models.CodelistCode.query.filter_by(
        codelist_code = codelist,
    	name = name
    ).first()
    if code: return code
    return False

def get_or_create_code(codelist, name):
    code = get_code_by_name(codelist, name)
    if code: return code.code
    return create_code({
        "codelist_code": codelist,
        "name": name,
        "code": normality.slugify(name)
    }).code

def create_code(data):
    codelistcode = models.CodelistCode()
    
    for attr, val in data.items():
        setattr(codelistcode, attr, val)
    db.session.add(codelistcode)
    db.session.commit()
    return codelistcode

def update_attr(data):
    codelistcode = models.CodelistCode.query.filter_by(
        id = data['id'],
    	codelist_code = data["codelist_code"]
    ).first()
    setattr(codelistcode, data['attr'], data['value'])
    db.session.add(codelistcode)
    db.session.commit()
    return codelistcode.id

def delete_code(data):
    check = models.ActivityCodelistCode.query.filter_by(
        codelist_code_id=data['id']).first() or models.ActivityFinancesCodelistCode.query.filter_by(
        codelist_code_id=data['id']).first()
    if check: return False
    codelistcode = models.CodelistCode.query.filter_by(
        id = data['id']
    ).first()
    db.session.delete(codelistcode)
    db.session.commit()
    return True
