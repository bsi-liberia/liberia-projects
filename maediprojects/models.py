import sqlalchemy as sa
import functools as ft
from maediprojects import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

cascade_relationship = ft.partial(
    sa.orm.relationship,
    cascade="all,delete",
    passive_deletes=True,
)

act_ForeignKey = ft.partial(
    sa.ForeignKey,
    ondelete="CASCADE"
)

class Organisation(db.Model):
    __tablename__ = 'organisation'
    organisation_name = sa.Column(sa.UnicodeText)
    organisation_ref = sa.Column(sa.UnicodeText)
    organisation_type = sa.Column(sa.UnicodeText)
    organisation_slug = sa.Column(sa.UnicodeText, 
                            primary_key=True)
    organisation_default_currency = sa.Column(sa.UnicodeText)
    organisation_contact_name = sa.Column(sa.UnicodeText)
    organisation_contact_email = sa.Column(sa.UnicodeText)
    organisation_contact_address = sa.Column(sa.UnicodeText)
    organisation_contact_phone = sa.Column(sa.UnicodeText)
    organisation_contact_website = sa.Column(sa.UnicodeText)
    budgets = cascade_relationship("OrgBudget")
    documents = cascade_relationship("OrgDoc")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class OrgBudget(db.Model):
    __tablename__ = 'organisationbudget'
    id = sa.Column(sa.Integer, primary_key=True)
    organisation_slug = sa.Column(
            sa.ForeignKey('organisation.organisation_slug'), 
            nullable=False)
    start_date = sa.Column(sa.Date)
    end_date = sa.Column(sa.Date)
    value = sa.Column(sa.Float(precision=2))

    def as_dict(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
    
class OrgDoc(db.Model):
    __tablename__ = 'organisationdoc'
    id = sa.Column(sa.Integer, primary_key=True)
    organisation_slug = sa.Column(sa.Integer, 
            sa.ForeignKey('organisation.organisation_slug'), 
            nullable=False)
    url = sa.Column(sa.UnicodeText)
    title = sa.Column(sa.UnicodeText)
    format = sa.Column(sa.UnicodeText)
    category = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrgConvertedFile(db.Model):
    __tablename__ = 'organisationfile'
    id = sa.Column(sa.Integer, primary_key=True)
    organisation_slug = sa.Column(
            sa.ForeignKey('organisation.organisation_slug'), 
            nullable=False)
    file_type_code = sa.Column(
            sa.ForeignKey('file_type.code'), 
            nullable=False)
    file_type = sa.orm.relationship(
                        "FileType")
    file_name = sa.Column(sa.UnicodeText)
    file_generated_date = sa.Column(sa.DateTime)
    file_published = sa.Column(sa.Boolean,
                               default=False)
    file_published_date = sa.Column(sa.DateTime)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class FileType(db.Model):
    __tablename__ = 'file_type'
    code = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Codelist(db.Model):
    __tablename__ = 'codelist'
    code = sa.Column(sa.UnicodeText, primary_key=True) # should be a slug
    name = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class CodelistCode(db.Model):
    __tablename__ = 'codelistcode'
    code = sa.Column(sa.UnicodeText, primary_key=True) # should be a slug
    name = sa.Column(sa.UnicodeText)
    codelist_code = sa.Column(sa.Integer,
            sa.ForeignKey('codelist.code'),
            nullable=False)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class Activity(db.Model):
    __tablename__ = 'activity'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
            act_ForeignKey('maediuser.id'),
            nullable=False,
            index=True)
    code = sa.Column(sa.UnicodeText)
    title = sa.Column(sa.UnicodeText)
    description = sa.Column(sa.UnicodeText)
    start_date = sa.Column(sa.Date)
    end_date = sa.Column(sa.Date)
    executing_org = sa.Column(sa.UnicodeText) # ADDED
    implementing_org = sa.Column(sa.UnicodeText) # ADDED
    recipient_country_code = sa.Column(
            act_ForeignKey('country.code'),
            nullable=False,
            index=True)
    recipient_country = sa.orm.relationship("Country")
    dac_sector = sa.Column(sa.UnicodeText)
    cicid_sector = sa.Column(sa.UnicodeText)
    collaboration_type = sa.Column(sa.UnicodeText) # ADDED
    finance_type = sa.Column(sa.UnicodeText) # ADDED
    tied_status = sa.Column(sa.UnicodeText) # ADDED
    flow_type = sa.Column(sa.UnicodeText)
    aid_type = sa.Column(sa.UnicodeText)
    activity_status = sa.Column(sa.UnicodeText)
    total_commitments = sa.Column(sa.Float(precision=2))
    total_disbursements = sa.Column(sa.Float(precision=2))
    updated_date = sa.Column(sa.DateTime, default=datetime.datetime.utcnow) # ADDED
    results = cascade_relationship("ActivityResult")
    locations = cascade_relationship("ActivityLocation")
    finances = cascade_relationship("ActivityFinances")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class ActivityLocation(db.Model):
    __tablename__ = 'activitylocation'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer,
            sa.ForeignKey('activity.id'),
            nullable=False)
    location_id = sa.Column(sa.Integer,
            sa.ForeignKey('location.id'),
            nullable=False)
    locations = sa.orm.relationship("Location")

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data

class ActivityFinances(db.Model):
    __tablename__ = 'activityfinances'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer, 
            sa.ForeignKey('activity.id'), 
            nullable=False)
    transaction_date = sa.Column(sa.Date)
    transaction_type = sa.Column(sa.UnicodeText)
    transaction_description = sa.Column(sa.UnicodeText)
    transaction_value = sa.Column(sa.Float(precision=2))

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Location(db.Model):
    __tablename__ = 'location'
    id = sa.Column(sa.Integer, primary_key=True)
    country = sa.Column(
            act_ForeignKey('country.code'),
            nullable=False,
            index=True)
    name = sa.Column(sa.UnicodeText)
    latitude = sa.Column(sa.UnicodeText)
    longitude = sa.Column(sa.UnicodeText)
    feature_code = sa.Column(sa.UnicodeText)
    admin1_code = sa.Column(sa.UnicodeText)
    admin2_code = sa.Column(sa.UnicodeText)
    admin3_code = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Country(db.Model):
    __tablename__ = 'country'
    code = sa.Column(sa.UnicodeText, primary_key=True)
    name = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class ActivityResult(db.Model):
    __tablename__ = 'activityresult'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey('activity.id'), 
            nullable=False,
            index=True)
    result_title = sa.Column(sa.UnicodeText)
    result_description = sa.Column(sa.UnicodeText)
    result_type = sa.Column(sa.Integer)
    indicators = cascade_relationship(
                        "ActivityResultIndicator")
    activity = sa.orm.relationship(
                        "Activity")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class ActivityResultIndicator(db.Model):
    __tablename__ = 'activityresultindicator'
    id = sa.Column(sa.Integer, primary_key=True)
    result_id = sa.Column(
            act_ForeignKey('activityresult.id'), 
            nullable=False,
            index=True)
    indicator_title = sa.Column(sa.UnicodeText)
    indicator_description = sa.Column(sa.UnicodeText)
    baseline_year = sa.Column(sa.Date)
    baseline_value = sa.Column(sa.UnicodeText)
    baseline_comment = sa.Column(sa.UnicodeText)
    periods = cascade_relationship(
                        "ActivityResultIndicatorPeriod")
    result = sa.orm.relationship("ActivityResult")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class ActivityResultIndicatorPeriod(db.Model):
    __tablename__ = 'activityresultindicatorperiod'
    id = sa.Column(sa.Integer, primary_key=True)
    indicator_id = sa.Column(
            act_ForeignKey('activityresultindicator.id'), 
            nullable=False,
            index=True)
    period_start = sa.Column(sa.Date)
    period_end = sa.Column(sa.Date)
    target_value = sa.Column(sa.UnicodeText)
    target_comment = sa.Column(sa.UnicodeText)
    actual_value = sa.Column(sa.UnicodeText)
    actual_comment = sa.Column(sa.UnicodeText)
    result_indicator = sa.orm.relationship("ActivityResultIndicator")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class User(db.Model):
    __tablename__ = 'maediuser'
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.UnicodeText, nullable=False)
    name = sa.Column(sa.UnicodeText)
    email_address = sa.Column(sa.UnicodeText)
    reset_password_key = sa.Column(sa.UnicodeText)
    pw_hash = db.Column(sa.String(255))
    organisation = sa.Column(sa.UnicodeText)
    administrator = sa.Column(sa.Boolean,
                               default=False)
    recipient_country_code = sa.Column(
            act_ForeignKey('country.code'),
            nullable=False,
            index=True) # we set a default country code for each user
    recipient_country = sa.orm.relationship("Country")
    permissions = db.relationship("UserPermission",
                    cascade="all, delete-orphan",
                    passive_deletes=True)
    __table_args__ = (sa.UniqueConstraint('username',),)

    def setup(self,
                 username,
                 password,
                 name,
                 email_address=None,
                 organisation=None,
                 recipient_country_code=None,
                 administrator=False,
                 id=None):
        self.username = username
        self.pw_hash = generate_password_hash(password)
        self.name = name
        self.email_address = email_address
        self.organisation = organisation
        self.recipient_country_code = recipient_country_code
        self.administrator = administrator
        if id is not None:
            self.id = id
    
    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
        
class UserPermission(db.Model):
    __tablename__ = 'userpermission'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer,
                        sa.ForeignKey('maediuser.id',
                        ondelete='CASCADE'))
    permission_name = sa.Column(sa.UnicodeText)

    def setup(self,
             user_id,
             permission_name=None,
             id=None):
        self.user_id = user_id
        self.permission_name = permission_name
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}