import os

from flask import url_for
import pytest

from maediprojects import create_app
from maediprojects.extensions import db as _db
from maediprojects.query.user import addUser, deleteUser
from maediprojects.query.setup import create_codes_codelists
from tests.config import SQLALCHEMY_DATABASE_URI as TEST_DATABASE_URI


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    app = create_app('tests.config')

    # Establish an application context before running the tests.
    ctx = app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database."""
    def teardown():
        _db.session.remove()
        _db.drop_all()

    _db.app = app
    _db.create_all()

    create_codes_codelists()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='session')
def client(app, db):
    """A Flask test client. An instance of :class:`flask.testing.TestClient`
    by default.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def admin(request, app, client):
    user_dict = app.config["ADMIN_USER"]
    user = addUser(user_dict)
    client.post(url_for('users.login'), data=user_dict)

    def teardown():
        deleteUser(user_dict['username'])

    request.addfinalizer(teardown)

    return user


@pytest.fixture(scope='function')
def user(request, app, client):
    user_dict = app.config["USER"]
    user = addUser(user_dict)
    client.post(url_for('users.login'), data=user_dict)

    def teardown():
        deleteUser(user_dict['username'])

    request.addfinalizer(teardown)

    return user
