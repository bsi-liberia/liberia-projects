from maediprojects import db, models
import datetime

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
    db.session.add(codelistcode)
    db.session.commit()
    return True

def delete_code(data):
    codelistcode = models.CodelistCode.query.filter_by(
        code = data['code'],
    	codelist_code = data["codelist_code"]
    ).first()
    db.session.delete(codelistcode)
    db.session.commit()
    return True
