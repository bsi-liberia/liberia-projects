import datetime
import functools as ft

import sqlalchemy as sa
from sqlalchemy import func, union_all
from sqlalchemy.orm import validates, aliased
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user

from maediprojects.extensions import db


cascade_relationship = ft.partial(
    sa.orm.relationship,
    cascade="all,delete",
    passive_deletes=True,
)

act_ForeignKey = ft.partial(
    sa.ForeignKey,
    ondelete="CASCADE"
)

# Adapted from here:
# https://stackoverflow.com/questions/42552696/sqlalchemy-nearest-datetime
def get_closest_date(the_date, the_currency):
    """
    Returns the highest-scoring conversion rate. The score is derived from:
      * the proximity to the requested date `the_date` for a given
        currency `the_currency`
      * multiplied by a score given to each exchange rate source.

    For example, we set FRED (daily) rates to have a score of 1 and
    OECD (monthly) rates to have a score of 33. This means a FRED rate can
    have a date up to 33 days further away from the requested date to score
    the same as an OECD rate on the same day as the requested date.
    """
    greater = db.session.query(ExchangeRate
        ).filter(ExchangeRate.rate_date > the_date,
            Currency.code == the_currency
        ).join(Currency
        ).order_by(ExchangeRate.rate_date.asc()).limit(30).subquery().select()

    lesser = db.session.query(ExchangeRate
        ).filter(ExchangeRate.rate_date <= the_date,
            Currency.code == the_currency
        ).join(Currency
        ).order_by(ExchangeRate.rate_date.desc()).limit(30).subquery().select()

    the_union = union_all(lesser, greater).alias()
    the_alias = aliased(ExchangeRate, the_union)
    abs_diff = func.abs(func.julianday(getattr(the_alias, "rate_date")) - func.julianday(the_date))
    score_alias = aliased(ExchangeRateSource, the_union)
    abs_score = (func.abs(getattr(score_alias, "weight")) *
        1+(func.abs(func.julianday(getattr(the_alias, "rate_date")) -
            func.julianday(the_date))))

    return db.session.query(the_alias,
        abs_diff,
        abs_score
        ).join(ExchangeRateSource, the_alias.exchangeratesource_id == ExchangeRateSource.id
        ).join(Currency, the_alias.currency_code == Currency.code
        ).filter(Currency.code == the_currency
        ).order_by(abs_score.asc()
        ).first()

def fwddata_query(_self, fiscalyear_modifier):
    return db.session.query(
            func.sum(ActivityForwardSpend.value).label("value"),
            func.STRFTIME('%Y',
                func.DATE(ActivityForwardSpend.period_start_date,
                    'start of month', '-{} month'.format(fiscalyear_modifier))
                ).label("fiscal_year"),
            case(
                [
                    (func.STRFTIME('%m', func.DATE(ActivityForwardSpend.period_start_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('01','02','03')), 'Q1'),
                    (func.STRFTIME('%m', func.DATE(ActivityForwardSpend.period_start_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('04','05','06')), 'Q2'),
                    (func.STRFTIME('%m', func.DATE(ActivityForwardSpend.period_start_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('07','08','09')), 'Q3'),
                    (func.STRFTIME('%m', func.DATE(ActivityForwardSpend.period_start_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('10','11','12')), 'Q4'),
                ]
            ).label("fiscal_quarter")
        ).filter(
            ActivityForwardSpend.activity_id == _self.id,
            ActivityForwardSpend.value != 0
        ).group_by("fiscal_quarter", "fiscal_year"
        ).order_by(ActivityForwardSpend.period_start_date.desc()
        ).all()


def fydata_query(_self, fiscalyear_modifier, _transaction_types):
    return db.session.query(
            func.sum(ActivityFinances.transaction_value).label("value"),
            func.STRFTIME('%Y',
                func.DATE(ActivityFinances.transaction_date,
                    'start of month', '-{} month'.format(fiscalyear_modifier))
                ).label("fiscal_year"),
            case(
                [
                    (func.STRFTIME('%m', func.DATE(ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('01','02','03')), 'Q1'),
                    (func.STRFTIME('%m', func.DATE(ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('04','05','06')), 'Q2'),
                    (func.STRFTIME('%m', func.DATE(ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('07','08','09')), 'Q3'),
                    (func.STRFTIME('%m', func.DATE(ActivityFinances.transaction_date,
                      'start of month', '-{} month'.format(fiscalyear_modifier))
                        ).in_(('10','11','12')), 'Q4'),
                ]
            ).label("fiscal_quarter")
        ).filter(
            ActivityFinances.activity_id == _self.id,
            ActivityFinances.transaction_value != 0,
            ActivityFinances.transaction_type.in_(_transaction_types)
        ).group_by("fiscal_quarter", "fiscal_year"
        ).order_by(ActivityFinances.transaction_date.desc()
        ).all()


class Currency(db.Model):
    __tablename__ = 'currency'
    code = sa.Column(sa.UnicodeText,
        nullable=False, primary_key=True)
    name = sa.Column(sa.UnicodeText,
        nullable=False)

    def as_dict(self):
        return ({c.name: getattr(self, c.name) for c in self.__table__.columns})


class ExchangeRateSource(db.Model):
    __tablename__ = 'exchangeratesource'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.UnicodeText, nullable=False)
    weight = sa.Column(sa.Float,
        default=1, nullable=False)

    def as_dict(self):
        return ({c.name: getattr(self, c.name) for c in self.__table__.columns})


class ExchangeRate(db.Model):
    __tablename__ = 'exchangerate'
    id = sa.Column(sa.Integer, primary_key=True)
    exchangeratesource_id = sa.Column(
        act_ForeignKey('exchangeratesource.id'),
        nullable=False, index=True)
    exchangeratesource = sa.orm.relationship("ExchangeRateSource")
    currency_code = sa.Column(
        act_ForeignKey('currency.code'),
        nullable=False, index=True)
    currency = sa.orm.relationship("Currency")
    rate_date = sa.Column(sa.Date,
        nullable=False, index=True)
    rate = sa.Column(sa.Float, nullable=False)

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data


class ActivityDocumentLink(db.Model):
    __tablename__ = 'activitydocumentlink'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
        act_ForeignKey('activity.id'),
        nullable=False, index=True)
    title = sa.Column(sa.UnicodeText)
    url = sa.Column(sa.UnicodeText)
    categories = sa.orm.relationship("ActivityDocumentLinkCategory",
            cascade="all, delete-orphan")
    document_date = sa.Column(sa.Date)

    def as_dict(self):
        return ({c.name: getattr(self, c.name) for c in self.__table__.columns})


class ActivityDocumentLinkCategory(db.Model):
    __tablename__ = 'activitydocumentlinkcategory'
    id = sa.Column(sa.Integer, primary_key=True)
    activitydocumentlink_id = sa.Column(
        act_ForeignKey('activitydocumentlink.id'),
        nullable=False, index=True)
    code = sa.Column(sa.UnicodeText)


class Activity(db.Model):
    __tablename__ = 'activity'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
            act_ForeignKey('maediuser.id'),
            nullable=False,
            index=True)
    user = sa.orm.relationship("User")
    code = sa.Column(sa.UnicodeText)
    title = sa.Column(sa.UnicodeText)
    description = sa.Column(sa.UnicodeText)
    start_date = sa.Column(sa.Date)
    end_date = sa.Column(sa.Date)
    organisations = sa.orm.relationship("ActivityOrganisation",
            cascade="all, delete-orphan")
    reporting_org_id = sa.Column(
            act_ForeignKey('organisation.id'),
            nullable=False,
            index=True)
    reporting_org = sa.orm.relationship("Organisation",
            foreign_keys=[reporting_org_id])
    implementing_org = sa.Column(sa.UnicodeText) # ADDED
    recipient_country_code = sa.Column(
            act_ForeignKey('country.code'),
            nullable=False,
            index=True)
    recipient_country = sa.orm.relationship("Country")
    dac_sector = sa.Column(sa.UnicodeText)
    #local_sector = sa.Column(
    #        act_ForeignKey('codelistcode.code'),
    #        nullable=False,
    #        index=True)
    collaboration_type = sa.Column(sa.UnicodeText) # ADDED
    finance_type = sa.Column(sa.UnicodeText) # ADDED
    tied_status = sa.Column(sa.UnicodeText) # ADDED
    flow_type = sa.Column(sa.UnicodeText)
    aid_type = sa.Column(sa.UnicodeText)
    activity_status = sa.Column(sa.UnicodeText)
    total_commitments = sa.Column(sa.Float(precision=2))
    total_disbursements = sa.Column(sa.Float(precision=2))
    created_date = sa.Column(sa.DateTime, default=datetime.datetime.utcnow) # ADDED
    updated_date = sa.Column(sa.DateTime, default=datetime.datetime.utcnow) # ADDED
    results = sa.orm.relationship("ActivityResult",
            cascade="all, delete-orphan")
    locations = sa.orm.relationship("ActivityLocation",
            cascade="all, delete-orphan")
    finances = sa.orm.relationship("ActivityFinances",
            cascade="all, delete-orphan")
    forwardspends = sa.orm.relationship("ActivityForwardSpend",
            cascade="all, delete-orphan")
    classifications = sa.orm.relationship("ActivityCodelistCode",
            cascade="all, delete-orphan")
    milestones = sa.orm.relationship("ActivityMilestone",
            cascade="all, delete-orphan")
    counterpart_funding = sa.orm.relationship("ActivityCounterpartFunding",
            cascade="all, delete-orphan")
    domestic_external = sa.Column(sa.UnicodeText)

    documents = sa.orm.relationship("ActivityDocumentLink",
            cascade="all, delete-orphan")

    @hybrid_property
    def permissions(self):
        # TODO eventually this will vary by activity, as permissions can be
        # selective for different organisations.
        def _check_org_permission():
            org_permission = self.reporting_org_id in current_user.permissions_dict["organisations"]
            if org_permission:
                return current_user.permissions_dict["organisations"][self.reporting_org_id]["permission_value"]
            return False
        op = _check_org_permission()
        return {
        "edit": (bool(current_user.permissions_dict["domestic_external_edit"] != "none") or (op=="edit")),
        "view": (bool(current_user.permissions_dict["domestic_external"] != "none") or (op in ("view", "edit")))
        }

    implementing_organisations = sa.orm.relationship("Organisation",
        secondary="activityorganisation",
        secondaryjoin="""and_(ActivityOrganisation.role==4,
            ActivityOrganisation.organisation_id==Organisation.id)"""
        )

    funding_organisations = sa.orm.relationship("Organisation",
        secondary="activityorganisation",
        secondaryjoin="""and_(ActivityOrganisation.role==1,
            ActivityOrganisation.organisation_id==Organisation.id)"""
        )

    @hybrid_property
    def total_commitments(self):
        return db.session.query(sa.func.sum(ActivityFinances.transaction_value)
                        ).filter(ActivityFinances.transaction_type==u"C",
                         ActivityFinances.activity_id==self.id).first()[0]
    @hybrid_property
    def total_disbursements(self):
        return db.session.query(sa.func.sum(ActivityFinances.transaction_value)
                        ).filter(ActivityFinances.transaction_type==u"D",
                         ActivityFinances.activity_id==self.id).first()[0]

    @hybrid_property
    def commitments(self):
        return ActivityFinances.query.filter(ActivityFinances.transaction_value!=0,
                                             ActivityFinances.transaction_type==u"C",
                                             ActivityFinances.activity_id==self.id).all()
    @hybrid_property
    def disbursements(self):
        return ActivityFinances.query.filter(ActivityFinances.transaction_value!=0,
                                             ActivityFinances.transaction_type==u"D",
                                             ActivityFinances.activity_id==self.id).all()

    def FY_disbursements_for_FY(self, FY):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        result = db.session.query(
                func.sum(ActivityFinances.transaction_value).label("value")
            ).filter(
                ActivityFinances.activity_id == self.id,
                ActivityFinances.transaction_type.in_((u'D', u'E')),
                func.STRFTIME('%Y',
                    func.DATE(ActivityFinances.transaction_date,
                        'start of month', '-{} month'.format(fiscalyear_modifier))
                    ) == FY
            ).scalar()
        if result is None: return 0.00
        return result

    def FY_forwardspends_for_FY(self, FY):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        result = db.session.query(
                func.sum(ActivityForwardSpend.value).label("value")
            ).filter(
                ActivityForwardSpend.activity_id == self.id,
                func.STRFTIME('%Y',
                    func.DATE(ActivityForwardSpend.period_start_date,
                        'start of month', '-{} month'.format(fiscalyear_modifier))
                    ) == FY
            ).scalar()
        if result is None: return 0.00
        return result

    def FY_counterpart_funding_for_FY(self, FY):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        result = db.session.query(
                func.sum(ActivityCounterpartFunding.required_value).label("value")
            ).filter(
                ActivityCounterpartFunding.activity_id == self.id,
                func.STRFTIME('%Y',
                    func.DATE(ActivityCounterpartFunding.required_date,
                        'start of month', '-{} month'.format(fiscalyear_modifier))
                    ) == FY
            ).scalar()
        if result is None: return 0.00
        return result

    @hybrid_property
    def FY_disbursements_dict(self):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        fydata = fydata_query(self, fiscalyear_modifier, (u'D', u'E'))

        return {
                    "{} {} (D)".format(fyval.fiscal_year, fyval.fiscal_quarter): {
                    "fiscal_year": fyval.fiscal_year,
                    "fiscal_quarter": fyval.fiscal_quarter,
                    "value": round(fyval.value, 4)
                    }
                    for fyval in fydata
                }

    @hybrid_property
    def FY_commitments_dict(self):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        fydata = fydata_query(self, fiscalyear_modifier, (u'C'))
        return {
                    "{} {} (C)".format(fyval.fiscal_year, fyval.fiscal_quarter): {
                    "fiscal_year": fyval.fiscal_year,
                    "fiscal_quarter": fyval.fiscal_quarter,
                    "value": round(fyval.value, 4)
                    }
                    for fyval in fydata
                }

    @hybrid_property
    def FY_forward_spend_dict(self):
        fiscalyear_modifier = 6 #FIXME this is just for Liberia
        fydata = fwddata_query(self, fiscalyear_modifier)
        return {
                    "{} {} (MTEF)".format(fyval.fiscal_year, fyval.fiscal_quarter): {
                    "fiscal_year": fyval.fiscal_year,
                    "fiscal_quarter": fyval.fiscal_quarter,
                    "value": round(fyval.value, 4)
                    }
                    for fyval in fydata
                }

    @hybrid_property
    def classification_data(self):
        def append_path(root, classification):
            if classification:
                sector = root.setdefault("{}".format(classification.codelist_code.codelist.code),
                    { "entries": [],
                      "name": classification.codelist_code.codelist.name,
                      "code": classification.codelist_code.codelist.code,
                      "id": classification.id
                    }
                )
                sector["entries"].append(classification)
        root = {}
        for s in self.classifications: append_path(root, s)
        return root

    @hybrid_property
    def milestones_data(self):
        all_milestones = Milestone.query.filter_by(
            domestic_external = self.domestic_external
        ).order_by(Milestone.milestone_order
        ).all()

        ms_achieved = dict(map(lambda ms: (ms.milestone.id, ms.achieved), self.milestones))
        ms_achieved_notes = dict(map(lambda ms: (ms.milestone.id, ms.notes), self.milestones))

        ms = list(map(lambda ms: {
            "name": ms.name,
            "id": ms.id,
            "notes": ms_achieved_notes.get(ms.id, ""),
            "achieved": {
                True: {"status": True, "name": "Completed", "icon": "glyphicon-ok", "colour": "success"},
                False: {"status": False, "name": "Pending", "icon": "glyphicon-remove", "colour": "warning"},
                }[bool(ms_achieved.get(ms.id, False))]}, all_milestones))
        return ms

    def as_dict(self):
        return ({c.name: getattr(self, c.name) for c in self.__table__.columns})

    def as_jsonable_dict(self):
        ret_data = {}
        ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
        #'user', 'organisations', 'reporting_org', 'recipient_country', 'results', 'locations', 'finances', 'forwardspends', 'classifications'
        ret_data.update({key: getattr(self, key).as_dict() for key in ['reporting_org']})
        [ret_data.update({key: [c.as_dict() for c in getattr(self, key)]}) for key in ['finances', 'locations', 'classifications', 'organisations', 'implementing_organisations']]
        return ret_data

class ActivityFinances(db.Model):
    __tablename__ = 'activityfinances'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer,
            sa.ForeignKey('activity.id'),
            nullable=False,
            index=True)
    activity = sa.orm.relationship("Activity")
    currency = sa.Column(sa.UnicodeText, default=u"USD")
    transaction_date = sa.Column(sa.Date)
    transaction_type = sa.Column(sa.UnicodeText,
            index=True)
    transaction_description = sa.Column(sa.UnicodeText)
    transaction_value = sa.Column(sa.Float(precision=2))
    finance_type = sa.Column(sa.UnicodeText)
    aid_type = sa.Column(sa.UnicodeText)
    provider_org_id = sa.Column(sa.Integer,
            sa.ForeignKey('organisation.id'),
            nullable=False)
    provider_org = sa.orm.relationship("Organisation",
            foreign_keys=[provider_org_id])
    receiver_org_id = sa.Column(sa.Integer,
            sa.ForeignKey('organisation.id'),
            nullable=False)
    receiver_org = sa.orm.relationship("Organisation",
            foreign_keys=[receiver_org_id])
    classifications = sa.orm.relationship("ActivityFinancesCodelistCode",
            cascade="all, delete-orphan")

    transaction_value_original = sa.Column(sa.Float(precision=2),
        default=0, nullable=False)
    currency_automatic = sa.Column(sa.Boolean,
        default=True, nullable=False)
    currency_source = sa.Column(sa.UnicodeText,
        default=u"USD", nullable=False)
    currency_rate = sa.Column(sa.Float,
        default=1.0, nullable=False)
    currency_value_date = sa.Column(sa.Date)

    @validates("currency_rate")
    def update_transaction_value_rate(self, key, currency_rate):
        if self.transaction_value_original and currency_rate:
            self.transaction_value = float(currency_rate)*float(self.transaction_value_original)
        return currency_rate

    @validates("transaction_value_original")
    def update_transaction_value_original(self, key, transaction_value_original):
        if self.currency_rate and transaction_value_original:
            self.transaction_value = float(self.currency_rate)*float(transaction_value_original)
        return transaction_value_original

    @hybrid_property
    def disaggregated_transactions(self):
        _funding_orgs = [self.provider_org,self.provider_org] or self.activity.funding_organisations
        funding_pcts = [{"pct": 1.0/len(_funding_orgs), "obj": f} for f in _funding_orgs]
        _receiving_orgs = [self.receiver_org] or self.activity.implementing_organisations
        receiving_pcts = [{"pct": 1.0/len(_receiving_orgs), "obj": r} for r in _receiving_orgs]
        class DisaggregatedTransaction(ActivityFinances):
            def __init__(self,f,r,transaction):
                pct_modifier = f["pct"]*r["pct"]
                self.activity = transaction.activity
                self.provider_org = f["obj"],
                self.receiver_org = r["obj"],
                self.value = transaction.transaction_value*pct_modifier
        return [DisaggregatedTransaction(f,r,self)
            for r in receiving_pcts
            for f in funding_pcts]

    @hybrid_property
    def mtef_sector(self):
        mtef = ActivityFinancesCodelistCode.query.filter_by(
                    activityfinance_id = self.id,
                    codelist_id = u"mtef-sector"
                    ).first()
        if mtef: return mtef.codelist_code_id
        return ""

    def as_dict(self):
        ret_data = {}
        ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
        ret_data.update({key: getattr(self, key).as_dict() for key in ['provider_org', 'receiver_org']})
        [ret_data.update({key: [c.as_dict() for c in getattr(self, key)]}) for key in ['classifications']]
        ret_data["mtef_sector"] = self.mtef_sector
        return ret_data

class ActivityForwardSpend(db.Model):
    __tablename__ = 'forwardspend' # 'activityforwardspend'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
        act_ForeignKey("activity.id"),
        nullable=False)
    value = sa.Column(sa.Float(precision=2))
    value_date = sa.Column(sa.Date)
    value_currency = sa.Column(sa.UnicodeText)
    period_start_date = sa.Column(sa.Date)
    period_end_date = sa.Column(sa.Date)

    __table_args__ = (sa.UniqueConstraint('activity_id','period_start_date'),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Country(db.Model):
    __tablename__ = 'country'
    code = sa.Column(sa.UnicodeText, primary_key=True)
    name = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Location(db.Model):
    __tablename__ = 'location'
    id = sa.Column(sa.Integer, primary_key=True)
    geonames_id = sa.Column(sa.Integer)
    country_code = sa.Column(
            act_ForeignKey('country.code'),
            nullable=False,
            index=True)
    country = sa.orm.relationship("Country")
    name = sa.Column(sa.UnicodeText)
    latitude = sa.Column(sa.UnicodeText)
    longitude = sa.Column(sa.UnicodeText)
    feature_code = sa.Column(sa.UnicodeText)
    admin1_code = sa.Column(sa.UnicodeText)
    admin2_code = sa.Column(sa.UnicodeText)
    admin3_code = sa.Column(sa.UnicodeText)

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
    activity = sa.orm.relationship("Activity")

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data

class Organisation(db.Model):
    __tablename__ = 'organisation'
    id = sa.Column(sa.Integer,
                            primary_key=True)
    code = sa.Column(sa.UnicodeText) # eventually rename to iati_code
    budget_code = sa.Column(sa.UnicodeText)
    name = sa.Column(sa.UnicodeText)
    acronym = sa.Column(sa.UnicodeText)
    _type = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ActivityOrganisation(db.Model):
    __tablename__ = 'activityorganisation'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer,
            sa.ForeignKey('activity.id'),
            nullable=False)
    organisation_id = sa.Column(sa.Integer,
            sa.ForeignKey('organisation.id'),
            nullable=False)
    organisation = sa.orm.relationship("Organisation")
    role = sa.Column(sa.Integer,
            nullable=False)
    percentage = sa.Column(sa.Float,
            default=100.00)
    __table_args__ = (sa.UniqueConstraint('activity_id','organisation_id', 'role'),)

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data

class Codelist(db.Model):
    __tablename__ = 'codelist'
    code = sa.Column(sa.UnicodeText, primary_key=True) # should be a slug
    name = sa.Column(sa.UnicodeText)
    __table_args__ = (sa.UniqueConstraint('code',),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class CodelistCode(db.Model):
    __tablename__ = 'codelistcode'
    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.UnicodeText)
    name = sa.Column(sa.UnicodeText)
    codelist_code = sa.Column(sa.Integer,
            sa.ForeignKey('codelist.code'),
            nullable=False)
    codelist = sa.orm.relationship("Codelist")
    __table_args__ = (sa.UniqueConstraint('code','codelist_code'),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ActivityCodelistCode(db.Model):
    __tablename__ = 'activitycodelistcode'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer,
            sa.ForeignKey('activity.id'),
            nullable=False)
    codelist_code_id = sa.Column(sa.Integer,
            sa.ForeignKey('codelistcode.id'),
            nullable=False)
    codelist_code = sa.orm.relationship("CodelistCode")
    percentage = sa.Column(sa.Float,
            default=100.00)
    __table_args__ = (sa.UniqueConstraint('activity_id','codelist_code_id'),)

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data

class ActivityFinancesCodelistCode(db.Model):
    __tablename__ = 'activityfinancescodelistcode'
    id = sa.Column(sa.Integer, primary_key=True)
    activityfinance_id = sa.Column(sa.Integer,
            sa.ForeignKey('activityfinances.id'),
            nullable=False)
    codelist_id = sa.Column(sa.Integer,
            sa.ForeignKey('codelist.code'),
            nullable=False)
    codelist_code_id = sa.Column(sa.Integer,
            sa.ForeignKey('codelistcode.id'),
            nullable=False)
    codelist_code = sa.orm.relationship("CodelistCode")
    __table_args__ = (sa.UniqueConstraint('activityfinance_id','codelist_id'),)

    def as_dict(self):
       ret_data = {}
       ret_data.update({c.name: getattr(self, c.name) for c in self.__table__.columns})
       ret_data.update({key: getattr(self, key).as_dict() for key in self.__mapper__.relationships.keys()})
       return ret_data

class Milestone(db.Model):
    __tablename__ = 'milestone'
    id = sa.Column(sa.Integer, primary_key=True)
    milestone_order = sa.Column(sa.Integer)
    name = sa.Column(sa.UnicodeText)
    domestic_external = sa.Column(sa.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ActivityMilestone(db.Model):
    __tablename__ = 'activitymilestone'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(
            act_ForeignKey('activity.id'),
            nullable=False,
            index=True)
    milestone_id = sa.Column(
            act_ForeignKey('milestone.id'),
            nullable=False,
            index=True)
    achieved = sa.Column(sa.Boolean)
    notes = sa.Column(sa.UnicodeText)
    activity = sa.orm.relationship(
                        "Activity")
    milestone = sa.orm.relationship(
                        "Milestone")

    __table_args__ = (sa.UniqueConstraint('activity_id','milestone_id'),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ActivityCounterpartFunding(db.Model):
    __tablename__ = 'activitycounterpartfunding'
    id = sa.Column(sa.Integer, primary_key=True)
    activity_id = sa.Column(sa.Integer,
            sa.ForeignKey('activity.id'),
            nullable=False,
            index=True)
    required_value = sa.Column(sa.Float(precision=2))
    required_date = sa.Column(sa.Date)
    budgeted = sa.Column(sa.Boolean, default=False)
    allotted = sa.Column(sa.Boolean, default=False)
    disbursed = sa.Column(sa.Boolean, default=False)

    __table_args__ = (sa.UniqueConstraint('activity_id','required_date'),)

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
    organisations = db.relationship("UserOrganisation",
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

    @hybrid_property
    def permissions_dict(self):
        permissions = dict(map(lambda p: (p.permission_name, p.permission_value), self.permissions))
        permissions["organisations"] = dict(map(lambda op: (op.organisation_id, op.as_dict()), self.organisations))
        return permissions

class UserPermission(db.Model):
    __tablename__ = 'userpermission'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer,
                        sa.ForeignKey('maediuser.id',
                        ondelete='CASCADE'))
    permission_name = sa.Column(sa.UnicodeText)
    permission_value = sa.Column(sa.UnicodeText)

    def setup(self,
             user_id,
             permission_name=None,
             id=None):
        self.user_id = user_id
        self.permission_name = permission_name
        self.permission_value = permission_value
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class UserOrganisation(db.Model):
    __tablename__ = 'userorganisation'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer,
                        sa.ForeignKey('maediuser.id',
                        ondelete='CASCADE'))
    permission_name = sa.Column(sa.UnicodeText)
    permission_value = sa.Column(sa.UnicodeText)
    organisation_id = sa.Column(sa.Integer,
            sa.ForeignKey('organisation.id'),
            nullable=False)
    organisation = sa.orm.relationship("Organisation")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
