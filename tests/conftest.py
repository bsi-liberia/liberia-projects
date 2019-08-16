import os

from flask import url_for
import pytest

from maediprojects import create_app, models
from maediprojects.extensions import db as _db
from maediprojects.query.user import addUser, deleteUser
from maediprojects.query.setup import create_codes_codelists, import_countries
from tests.config import SQLALCHEMY_DATABASE_URI as TEST_DATABASE_URI
from werkzeug.datastructures import FileStorage
from maediprojects.query.generate_xlsx import xlsx_to_csv, import_xls
from maediprojects.query import activity as qactivity
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import base64


@pytest.fixture(scope="session")
def app():
    """Session-wide test `Flask` application."""
    app = create_app('tests.config')
    app.testing = True

    with app.app_context() as client:
        _db.app = app
        _db.create_all()
        create_codes_codelists()
        import_countries(u"en")

        user_dict = app.config["ADMIN_USER"]
        user = addUser(user_dict)
        _db.session.commit()
        # Confirm everything was set up properly
        assert models.User.query.get(user.id).username == user_dict["username"]
        assert len(models.User.query.get(user.id).permissions) == 2
        assert models.User.query.get(user.id).permissions[0].permission_name == "domestic_external"
        assert models.User.query.get(user.id).permissions[1].permission_name == "domestic_external_edit"
        assert len(models.User.query.get(user.id).permissions_dict) == 3
        assert models.User.query.get(user.id).permissions_dict["organisations"] == {}
        with app.test_client() as client:
            client.post(url_for('users.login'), data=user_dict)
            import_test_data(user.id)
            time.sleep(1)
        yield app
        _db.session.close()
        _db.session.remove()
        _db.drop_all()


@pytest.mark.usefixtures("live_server")
class LiveServerClass:
    time.sleep(3)
    pass

@pytest.fixture()
def selenium_login(app, selenium):
    time.sleep(1)
    user_dict = app.config["ADMIN_USER"]
    selenium.get(url_for('users.login', _external=True))
    selenium.find_element_by_name("username").send_keys(user_dict["username"])
    selenium.find_element_by_name("password").send_keys(user_dict["password"])
    selenium.find_element_by_id("submit").click()
    wait = WebDriverWait(selenium, 10)
    element = wait.until(EC.title_is("Dashboard | Liberia Project Dashboard"))
    yield selenium


@pytest.fixture
def chrome_options(request, chrome_options):
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('w3c', False)
    chrome_options.set_capability('goog:loggingPrefs', { 'browser':'ALL' })
    return chrome_options


def import_test_data(user_id):
    filename = os.path.join("tests", "artefacts", "testdata.xlsx")
    with open(filename, "rb") as _file:
        _fakeUpload = FileStorage(
            stream=_file,
            filename="testdata.xlsx")
        data = xlsx_to_csv.getDataFromFile("testdata.xlsx", _file.read(), 0, True)
        for row in data:
            qactivity.create_activity_for_test(row, user_id)
    time.sleep(1)
    with open(filename, "rb") as _file:
        _fakeUpload = FileStorage(
            stream=_file,
            filename="testdata.xlsx")
        result = import_xls(
            input_file=_fakeUpload,
            column_name=u'2018 Q4 (D)'
        )
    time.sleep(1)


@pytest.fixture(scope='function')
def admin(request, app, client):
    user_dict = app.config["ADMIN_USER_2"]
    user = addUser(user_dict)
    # Confirm user created
    assert models.User.query.get(user.id)
    client.post(url_for('users.login'), data=user_dict)
    # Confirm login worked
    assert client.get(url_for('activities.dashboard')).status_code == 200
    def teardown():
        deleteUser(user_dict['username'])

    request.addfinalizer(teardown)

    return user


@pytest.fixture(scope='function')
def user(request, app, client):
    user_dict = app.config["USER"]
    user = addUser(user_dict)
    # Confirm user created
    assert models.User.query.get(user.id)
    client.post(url_for('users.login'), data=user_dict)
    # Confirm login worked
    assert client.get(url_for('activities.dashboard')).status_code == 200

    def teardown():
        deleteUser(user_dict['username'])

    request.addfinalizer(teardown)

    return user


def pytest_selenium_capture_debug(item, report, extra):
    for log_type in extra:
        if log_type["name"] == "Screenshot":
            content = base64.b64decode(log_type["content"].encode("utf-8"))
            with open(item.name + ".png", "wb") as f:
                f.write(content)
