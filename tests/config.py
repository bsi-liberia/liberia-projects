"""Settings module for test app."""
import os


basedir = os.path.abspath(os.path.dirname(__file__))


SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
TESTING = True
SECRET_KEY = 'not-so-secret-in-tests'
SQLALCHEMY_TRACK_MODIFICATIONS = False
ADMIN_USER = {
    "username": u"admin",
    "password": u"admin",
    "name": u"YOUR_NAME",
    "email_address": u"YOUR_EMAIL",
    "organisation": u"YOUR_ORG",
    "recipient_country_code": u"ML",
    "administrator": True
}
USER = {
    "username": u"user",
    "password": u"user",
    "name": u"YOUR_NAME",
    "email_address": u"YOUR_EMAIL",
    "organisation": u"YOUR_ORG",
    "recipient_country_code": u"ML",
    "administrator": False
}
