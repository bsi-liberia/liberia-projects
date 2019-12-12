import normality

from maediprojects import models
from maediprojects.extensions import db


def get_organisations():
    return models.Organisation.query.order_by(
        models.Organisation.name
    ).all()

def get_organisation_by_id(id):
    org = models.Organisation.query.filter_by(
    	id = id
    ).first()
    if org: return org
    return False

def get_organisation_by_code(code):
    org = models.Organisation.query.filter_by(
    	code = code
    ).first()
    if org: return org
    return False

def get_organisation_by_name(name):
    org = models.Organisation.query.filter_by(
    	name = name
    ).first()
    if org: return org
    return False

def get_organisation_types():
    types = [('gol', 'Government of Liberia'),
        ('donor', 'Donor'), ('ngo', 'NGO')]
    return list(map(lambda t: {"id": t[0], "name": t[1]}, types))

def get_reporting_orgs(user_id=None):
    if user_id:
        user = models.User.query.get(user_id)
        if user:
            return list(map(lambda uo: uo.organisation, user.organisations))
    return db.session.query(models.Organisation
        ).join(models.Activity, models.Activity.reporting_org_id==models.Organisation.id
        ).order_by(
            models.Organisation.name
        ).group_by(
            models.Organisation.name
        ).all()

def get_or_create_organisation(name):
    org = get_organisation_by_name(name)
    if org: return org.id
    return create_organisation({
        "name": name,
        "code": normality.slugify(name)
    }).id

def make_organisation(name, role):
    organisation_id = get_or_create_organisation(name)
    activity_org = models.ActivityOrganisation()
    activity_org.organisation_id = organisation_id
    activity_org.role = role
    return activity_org

def create_activity_organisation(activity_id, name, role):
    organisation_id = get_or_create_organisation(name)
    activity_org = models.ActivityOrganisation()
    activity_org.organisation_id = organisation_id
    activity_org.activity_id = activity_id
    activity_org.role = role
    db.session.add(activity_org)
    db.session.commit()
    return activity_org

def update_activity_organisation(activityorganisation_id, organisation_id):
    activity_org = models.ActivityOrganisation.query.filter_by(
        id = activityorganisation_id
    ).first()
    if not activity_org: return False
    activity_org.organisation_id = organisation_id
    db.session.add(activity_org)
    db.session.commit()
    return activity_org

def create_organisation(data):
    org = models.Organisation()

    for attr, val in data.items():
        setattr(org, attr, val)
    db.session.add(org)
    db.session.commit()
    return org

def update_attr(data):
    org = models.Organisation.query.filter_by(
        id = data['id']
    ).first()
    setattr(org, data['attr'], data['value'])
    db.session.add(org)
    db.session.commit()
    return True

def delete_org(data):
    # Ensure this org is not attached to any activities
    check = (models.Activity.query.filter_by(
        reporting_org_id = data['id']
    ).first() or
        models.ActivityOrganisation.query.filter_by(
        organisation_id = data['id']
    ).first() or
        models.ActivityFinances.query.filter((
                models.ActivityFinances.provider_org_id == data['id']
            ) | (models.ActivityFinances.receiver_org_id == data['id'])).first())
    if check: return False
    org = models.Organisation.query.filter_by(
        id = int(data['id'])
    ).first()
    db.session.delete(org)
    db.session.commit()
    return True
