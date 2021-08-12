import os

from flask import url_for
import pytest

from projectdashboard import create_app, models
from projectdashboard.extensions import db as _db
from projectdashboard.query.user import addUser, deleteUser
from projectdashboard.query.setup import create_codes_codelists, import_countries, import_responses, import_roles
from werkzeug.datastructures import FileStorage
from projectdashboard.query.generate_xlsx import xlsx_to_csv, import_xls, import_xls_mtef
from projectdashboard.query import activity as qactivity
from projectdashboard.query import admin as qadmin
from projectdashboard.query.location import import_locations_from_file
from flask_jwt_extended import (
    create_access_token
)
from flask_login import login_user

basedir = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture(scope="session")
def app():
    """Session-wide test `Flask` application."""

    app = create_app('tests.config')
    app.testing = True

    with app.app_context() as client:
        _db.app = app
        _db.create_all()
        create_codes_codelists()
        import_responses()
        import_countries(u"en")
        # This is very slow
        #import_locations_from_file(os.path.join(basedir, "artefacts", "LR.zip"), u"LR")
        import_roles()

        user_dict = app.config["USER"]
        user = addUser(user_dict)

        admin_dict = app.config["ADMIN_USER"]
        admin = addUser(admin_dict)
        assert models.User.query.get(admin.id).username == admin_dict["username"]

        fiscal_years = [{
            'from': app.config['EARLIEST_DATE'].isoformat(),
            'to': app.config['LATEST_DATE'].isoformat()
        }]
        qadmin.process_fiscal_years(fiscal_years)

        import_test_data(app, admin)
        yield app
        _db.session.close()
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def headers_admin(app, admin):
    return {
        'Authorization': 'Bearer {}'.format(
        create_access_token(identity=admin.username))
    }


@pytest.fixture()
def headers_user(app, user):
    return {
        'Authorization': 'Bearer {}'.format(
        create_access_token(identity=user.username))
    }


def import_test_data(app, user):
    client = app.test_client()
    ctx = app.test_request_context()
    ctx.push()
    with client:
        login_user(user)
        filename = os.path.join("tests", "artefacts", "testdata.xlsx")
        with open(filename, "rb") as _file:
            _fakeUpload = FileStorage(
                stream=_file,
                filename="testdata.xlsx")
            data = xlsx_to_csv.getDataFromFile("testdata.xlsx", _file.read(), 0, True)
            for row in data:
                qactivity.create_activity_for_test(row, user.id)
        with open(filename, "rb") as _file:
            _fakeUpload = FileStorage(
                stream=_file,
                filename="testdata.xlsx")
            result = import_xls(
                input_file=_fakeUpload,
                column_name='FY2019 Q1 (D)'
            )
        with open(filename, "rb") as _file:
            _fakeUpload = FileStorage(
                stream=_file,
                filename="testdata.xlsx")
            result = import_xls_mtef(
                input_file=_fakeUpload
            )


@pytest.fixture(scope='function')
def admin(request, app, client):
    user_dict = app.config["ADMIN_USER_2"]
    user = addUser(user_dict)
    # Confirm user created
    assert models.User.query.get(user.id)
    def teardown():
        deleteUser(user_dict['username'])
    request.addfinalizer(teardown)
    return user


@pytest.fixture(scope='function')
def user(request, app, client):
    user_dict = app.config["USER_2"]
    user = addUser(user_dict)
    # Confirm user created
    assert models.User.query.get(user.id)
    def teardown():
        deleteUser(user_dict['username'])
    request.addfinalizer(teardown)
    return user
