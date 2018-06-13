from maediprojects import db, models
import datetime
import normality

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
        code = data['code'],
    	codelist_code = data["codelist_code"]
    ).first()
    setattr(codelistcode, data['attr'], data['value'])
    """
    if data['codelist_code'] == 'funding-organisation':
        models.Activity.query.filter_by(
            funding_org_code
        )
    """
    db.session.add(codelistcode)
    db.session.commit()
    return True

def delete_code(data):
    check = models.Activity.query.filter((
        models.Activity.executing_org == data['code']
    ) | (
        models.Activity.local_sector == data['code']
    )).first()
    if check: return False
    codelistcode = models.CodelistCode.query.filter_by(
        code = data['code'],
    	codelist_code = data["codelist_code"]
    ).first()
    db.session.delete(codelistcode)
    db.session.commit()
    return True
