# -*- coding: UTF-8 -*-

import os

from flask import current_app
import normality
import unicodecsv

from maediprojects import models
from maediprojects.lib import codelists
from maediprojects.query import user as quser
from maediprojects.query import organisations as qorganisations
from maediprojects.extensions import db


basedir = os.path.abspath(os.path.dirname(__file__))


def import_responses():
    responses = [{
        'name': 'Data requested, but donor has not yet responded',
        'icon': 'fa fa-check-circle text-muted'
    },
    {
        'name': 'Donor responded, but has no spending in this period',
        'icon': 'far fa-check-circle text-success'
    },
    {
        'name': 'Donor responded with data',
        'icon': 'fa fa-check-circle text-success'
    },
    {
        'name': 'Donor refused request',
        'icon': 'fa fa-exclamation-circle text-danger'
    }]
    for response in responses:
        r = models.Response()
        r.name = unicode(response['name'])
        r.icon = unicode(response['icon'])
        db.session.add(r)
    db.session.commit()


def import_roles():
    roles = [
        {'slug': 'desk-officer', 'name': 'Desk Officer'},
        {'slug': 'manager', 'name': 'Manager'},
        {'slug': 'admin', 'name': 'Administrator'}
    ]
    for role in roles:
        r = models.Role()
        r.slug = unicode(role['slug'])
        r.name = unicode(role['slug'])
        db.session.add(r)
    db.session.commit()
    for user in models.User.query.all():
        if len(user.organisations) > 0:
            role = models.Role.query.filter_by(
                slug=u'desk-officer').first()
            user_role = models.UserRole()
            user_role.user_id = user.id
            user_role.role_id = role.id
            user.userroles = [user_role]
        elif user.administrator:
            role = models.Role.query.filter_by(
                slug=u'admin').first()
            user_role = models.UserRole()
            user_role.user_id = user.id
            user_role.role_id = role.id
            user.userroles = [user_role]
        db.session.add(user)
    db.session.commit()


def import_countries(language, country_code=None):
    countries = codelists.get_codelists(language)["Country"]
    if country_code is not None:
        countries = [c for c in countries if c["code"] == country_code]
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

    def add_organisation(organisation_data):
        for organisation in organisation_data:
            organisation['_type'] = u"donor"
            qorganisations.create_organisation(organisation)

    local_codelist_files = [
        {
            "name": u"Aligned Ministry / Agency",
            "filename": "aligned-ministry-agency.csv"
         },
        {
            "name": u"MTEF Sector",
            "filename": "mtef-sector.csv"
         },
        {
            "name": u"AfT Pillar",
            "filename": "aft-pillar.csv"
         },
        {
            "name": u"PAPD Pillar",
            "filename": "papd-pillar.csv"
         },
        {
            "name": u"SDG Goals",
            "filename": "sdg-goals.csv"
         }]

    for codelist_file in local_codelist_files:
        f = open(os.path.join(basedir, "../lib/data/local/", codelist_file["filename"]), "rb")
        csv = unicodecsv.DictReader(f)
        add_codelist(codelist_file["name"], csv)
        f.close()

    # Add organisations
    f = open(os.path.join(basedir, "../lib/data/local/", "organisation.csv"), "rb")
    csv = unicodecsv.DictReader(f)
    add_organisation(csv)
    f.close()

def create_user():
    data = current_app.config["ADMIN_USER"]
    if quser.addUser(data):
        return "OK"
    return "FAILED"
