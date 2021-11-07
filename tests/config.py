"""Settings module for test app."""
import os
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
TESTING = True
SECRET_KEY = 'not-so-secret-in-tests'
SQLALCHEMY_TRACK_MODIFICATIONS = False
ADMIN_USER = {
    "username": u"admin",
    "password": u"admin",
    "name": u"YOUR_NAME",
    "email_address": u"YOUR_EMAIL",
    "organisation": u"YOUR_ORG",
    "recipient_country_code": u"LR",
    "administrator": True,
    "view": u"both",
    "edit": u"both"
}
ADMIN_USER_2 = {
    "username": u"admin2",
    "password": u"admin2",
    "name": u"YOUR_NAME2",
    "email_address": u"YOUR_EMAIL2",
    "organisation": u"YOUR_ORG2",
    "recipient_country_code": u"LR",
    "administrator": True,
    "view": u"both",
    "edit": u"both"
}
USER = {
    "username": u"user",
    "password": u"user",
    "name": u"YOUR_NAME",
    "email_address": u"YOUR_USER_EMAIL",
    "organisation": u"YOUR_USER_ORG",
    "recipient_country_code": u"LR",
    "administrator": False,
    "view": u"external",
    "edit": u"none"
}
USER_2 = {
    "username": u"user2",
    "password": u"user2",
    "name": u"YOUR_NAME",
    "email_address": u"YOUR_USER_EMAIL2",
    "organisation": u"YOUR_USER_ORG2",
    "recipient_country_code": u"LR",
    "administrator": False,
    "view": u"external",
    "edit": u"none"
}
# The earliest date shown in many interfaces.
# Used to filter out partial data from a long / messy dataset.
EARLIEST_DATE = datetime.date(2013,1,1)
FY_EARLIEST_DATE = datetime.date(2000,7,1)
LATEST_DATE = datetime.date(2049,12,31)

SERVER_NAME = "0.0.0.0"
LIVESERVER_PORT=8943
selenium_capture_debug="ALWAYS"
RESERVE_CONTEXT_ON_EXCEPTION=True
