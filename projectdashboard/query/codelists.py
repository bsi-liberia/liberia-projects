import datetime

from flask_login import current_user
import normality

from projectdashboard import models
from projectdashboard.extensions import db


def get_code_by_name(codelist, name):
    code = models.CodelistCode.query.filter_by(
        codelist_code = codelist,
        name = name
    ).first()
    if code: return code
    return False

def get_code_by_id(codelist, code):
    code = models.CodelistCode.query.filter_by(
        codelist_code = codelist,
        code = code
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
