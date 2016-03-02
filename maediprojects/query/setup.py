from maediprojects import app, db, models
from maediprojects.lib import codelists
from maediprojects.query import user as quser
import normality

def setup():
    db.create_all()
    create_codes_codelists()
    import_countries()
    create_user()

def import_countries():
    countries = codelists.get_codelists()["Country"]
    for country in countries:
        if country["code"] == "": continue
        c = models.Country()
        c.code = country["code"]
        c.name = country["name"]
        db.session.add(c)
    db.session.commit()

def create_codes_codelists():
    def add_codelist_data(codelist_name, codelist_code):
        codelistcode = models.CodelistCode()
        codelistcode.code = codelist_code["code"]
        codelistcode.name = codelist_code["name"]
        codelistcode.codelist_code = normality.slugify(codelist_name)
        db.session.add(codelistcode)
    
    def add_codelist(codelist_name, codelist_data):
        codelist = models.Codelist()
        codelist.code = normality.slugify(codelist_name)
        codelist.name = codelist_name
        db.session.add(codelist)
        db.session.commit()
        
        for codelist_code in codelist_data:
            add_codelist_data(codelist_name, codelist_code)
        db.session.commit()

    CODELISTS = {
        "Extending Organisation": [
            {
                "code": "FR-3",
                "name": "MAEDI"
            },
            {
                "code": "FR-6",
                "name": "AFD"
            }
        ],
        "CICID sectors": [
            {
                "code": "1",
                "name": "Education"
            }
        ]
    }
    
    for codelist_name, codelist_data in CODELISTS.items():
        add_codelist(codelist_name, codelist_data)

def create_user():
    data = app.config["ADMIN_USER"]
    if quser.addUser(data):
        return "OK"
    return "FAILED"
