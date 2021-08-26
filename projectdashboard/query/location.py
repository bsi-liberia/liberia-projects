from io import StringIO
from zipfile import ZipFile

from flask_login import current_user
from sqlalchemy import *
import requests
import csv as unicodecsv

from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.query.activity_log import activity_updated


GEONAMES_URL = "http://download.geonames.org/export/dump/%s.zip"
GEONAMES_FIELDNAMES = ['geonameid', 'name', 'asciiname', 'alternatenames',
                       'latitude', 'longitude', 'feature_class', 'feature_code', 'country_code',
                       'cc2', 'admin1_code', 'admin2_code', 'admin3_code', 'admin4_code',
                       'population', 'elevation', 'dem', 'timezone', 'modification_date']
ALLOWED_FEATURE_CODES = ["ADM1", "ADM2", "ADM3"]


def get_countries_locations():
    return db.session.query(models.Location
                            ).distinct(models.Location.country_code
                                       ).group_by(models.Location.country_code)


def get_locations_country(country_code):
    locations = models.Location.query.filter(and_(
        models.Location.feature_code.in_((u"ADM1", u"ADM2")),
        models.Location.country_code == country_code
    )).order_by(
        models.Location.admin1_code,
        models.Location.feature_code
    ).all()
    return locations


def add_location(activity_id, location_id):
    checkL = models.ActivityLocation.query.filter_by(
        activity_id=activity_id,
        location_id=location_id
    ).first()
    if not checkL:
        aL = models.ActivityLocation()
        aL.activity_id = activity_id
        aL.location_id = location_id
        db.session.add(aL)
        db.session.commit()

        activity_updated(activity_id,
                         {
                             "user_id": current_user.id,
                             "mode": "add",
                             "target": "ActivityLocation",
                             "target_id": aL.id,
                             "old_value": None,
                             "value": {'location_id': location_id}
                         }
                         )
        return True
    return False


def delete_location(activity_id, location_id):
    checkL = models.ActivityLocation.query.filter_by(
        activity_id=activity_id,
        location_id=location_id
    ).first()
    if checkL:
        db.session.delete(checkL)
        db.session.commit()

        activity_updated(activity_id,
                         {
                             "user_id": current_user.id,
                             "mode": "delete",
                             "target": "ActivityLocation",
                             "target_id": checkL.id,
                             "old_value": {'location_id': location_id},
                             "value": None
                         }
                         )
        return True
    return False


def _process_locations_import(zipfile, country_code):
    with zipfile.open("{}.txt".format(country_code), 'r') as country_csv:
        csv_text = country_csv.read().decode("UTF-8")
        csv = unicodecsv.DictReader(csv_text,
                                    fieldnames=GEONAMES_FIELDNAMES,
                                    dialect='excel-tab',
                                    quoting=unicodecsv.QUOTE_NONE)
        for row in csv:
            if row["feature_code"] in ALLOWED_FEATURE_CODES:
                location = models.Location()
                location.geonames_id = row["geonameid"]
                location.country_code = country_code
                location.name = row["name"]
                location.latitude = row["latitude"]
                location.longitude = row["longitude"]
                location.feature_code = row["feature_code"]
                location.admin1_code = row["admin1_code"]
                location.admin2_code = row["admin2_code"]
                location.admin3_code = row["admin3_code"]
                db.session.add(location)
        db.session.commit()


# Called when setting up individual countries
def import_locations_from_file(file_path, country_code):
    """Downloads geolocations from Geonames."""
    #fn = open(file_path, "rb")
    with ZipFile(file_path) as zipfile:
        _process_locations_import(zipfile, country_code)


# Called when setting up individual countries
def import_locations(country_code):
    """Downloads geolocations from Geonames."""
    r = requests.get(GEONAMES_URL % country_code)
    zipfile = ZipFile(StringIO(r.content))

    _process_locations_import(zipfile, country_code)
