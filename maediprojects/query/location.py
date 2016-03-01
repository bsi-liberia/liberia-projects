from maediprojects import db, models
from sqlalchemy import *

def get_locations_country(country_code):
    locations = models.Location.query.filter(and_(
        models.Location.feature_code.in_(("ADM1", "ADM2")),
        models.Location.country==country_code
    )).order_by(
        models.Location.admin1_code,
        models.Location.feature_code
    ).all()
    return locations

def add_location(activity_id, location_id):
    checkL = models.ActivityLocation.query.filter_by(
        activity_id = activity_id,
        location_id = location_id
    ).first()
    if not checkL:
        aL = models.ActivityLocation()
        aL.activity_id = activity_id
        aL.location_id = location_id
        db.session.add(aL)
        db.session.commit()
        return True
    return False

def delete_location(activity_id, location_id):
    checkL = models.ActivityLocation.query.filter_by(
        activity_id = activity_id,
        location_id = location_id
    ).first()
    if checkL:
        db.session.delete(checkL)
        db.session.commit()
        return True
    return False
