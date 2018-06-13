# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
from maediprojects.lib import codelists
from maediprojects.query import user as quser
import normality
import unicodecsv
import os
basedir = os.path.abspath(os.path.dirname(__file__))

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
    
    local_codelist_files = [
        {
            "name": "Aligned Ministry / Agency",
            "filename": "aligned-ministry-agency.csv"
         },
        {
            "name": "MTEF Sector",
            "filename": "mtef-sector.csv"
         },
        {
            "name": "Funding Organisation",
            "filename": "funding-organisation.csv"
         }]
    
    for codelist_file in local_codelist_files:
        f = open(os.path.join(basedir, "../lib/data/local/", codelist_file["filename"]), "rb")
        csv = unicodecsv.DictReader(f)
        add_codelist(codelist_file["name"], csv)
        f.close()
    
    temp = {
        "Agenda For Transformation Pillar": [
            {
                "code": "1",
                "name": u"Peace, Security and Rule of Law"
            },
            {
                "code": "2",
                "name": u"Economic Transformation"
            },
            {
                "code": "3",
                "name": u"Human Development"
            },
            {
                "code": "4",
                "name": u"Governance and Public Institutions"
            },
            {
                "code": "5",
                "name": u"Cross-cutting"
            }
        ]
    }
    
    #for codelist_name, codelist_data in CODELISTS.items():
    #    add_codelist(codelist_name, codelist_data)

def create_user():
    data = app.config["ADMIN_USER"]
    if quser.addUser(data):
        return "OK"
    return "FAILED"
