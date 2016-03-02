from maediprojects import app, db, models
from maediprojects.lib import codelists
from maediprojects.query import user as quser
import normality
from StringIO import StringIO
from zipfile import ZipFile
import requests
import unicodecsv

GEONAMES_URL="http://download.geonames.org/export/dump/%s.zip"
GEONAMES_FIELDNAMES = ['geonameid', 'name', 'asciiname', 'alternatenames', 
'latitude', 'longitude', 'feature_class', 'feature_code', 'country_code', 
'cc2', 'admin1_code', 'admin2_code', 'admin3_code', 'admin4_code', 
'population', 'elevation', 'dem', 'timezone', 'modification_date']
ALLOWED_FEATURE_CODES = ["ADM1", "ADM2", "ADM3"]

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

# Called when setting up individual countries
def import_locations(country_code):
    """Downloads geolocations from Geonames."""
    r = requests.get(GEONAMES_URL % country_code)
    zipfile = ZipFile(StringIO(r.content))
    csv = unicodecsv.DictReader(zipfile.open("%s.txt" % country_code), 
                                fieldnames=GEONAMES_FIELDNAMES,
                                dialect='excel-tab')
    for row in csv:
        if row["feature_code"] in ALLOWED_FEATURE_CODES:
            location = models.Location()
            location.geonames_id = row["geonameid"]
            location.country = country_code
            location.name = row["name"]
            location.latitude = row["latitude"]
            location.longitude = row["longitude"]
            location.feature_code = row["feature_code"]
            location.admin1_code = row["admin1_code"]
            location.admin2_code = row["admin2_code"]
            location.admin3_code = row["admin3_code"]
            db.session.add(location)
    db.session.commit()