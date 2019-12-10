import os

from flask import url_for
import pytest

from maediprojects import create_app, models
from maediprojects.extensions import db as _db
from maediprojects.query.user import addUser, deleteUser
from maediprojects.query.setup import create_codes_codelists, import_countries, import_responses
from werkzeug.datastructures import FileStorage
from maediprojects.query.generate_xlsx import xlsx_to_csv, import_xls
from maediprojects.query import activity as qactivity
from maediprojects.query.location import import_locations_from_file
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import base64
import tempfile

basedir = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture(scope="session")
def app():
    """Session-wide test `Flask` application."""

    app = create_app('tests.config')
    db_fd, db_fn = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///{}".format(db_fn)
    app.testing = True

    with app.app_context() as client:
        _db.app = app
        _db.create_all()
        create_codes_codelists()
        import_responses()
        import_countries(u"en")
        import_locations_from_file(os.path.join(basedir, "artefacts", "LR.zip"), u"LR")
        print os.path.abspath(os.path.join(basedir, "artefacts", "LR.zip"))

        user_user_dict = app.config["USER"]
        user_user = addUser(user_user_dict)
        assert models.User.query.get(user_user.id).username == user_user_dict["username"]

        user_dict = app.config["ADMIN_USER"]
        user = addUser(user_dict)
        assert models.User.query.get(user.id).username == user_dict["username"]
        # Confirm everything was set up properly
        assert models.User.query.get(user.id).username == user_dict["username"]
        assert len(models.User.query.get(user.id).permissions) == 2
        assert models.User.query.get(user.id).permissions[0].permission_name == "view"
        assert models.User.query.get(user.id).permissions[1].permission_name == "edit"
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
        os.close(db_fd)
        os.unlink(db_fn)


@pytest.mark.usefixtures("live_server")
class LiveServerClass:
    pass

def _do_login(user_dict, selenium):
    selenium.get(url_for('users.login', _external=True))
    assert models.User.query.filter_by(username=user_dict["username"]).first()
    selenium.find_element_by_name("username").send_keys(user_dict["username"])
    selenium.find_element_by_name("password").send_keys(user_dict["password"])
    selenium.find_element_by_id("submit").click()
    wait = WebDriverWait(selenium, 10)
    element = wait.until(EC.title_is("Dashboard | Liberia Project Dashboard"))
    return selenium


@pytest.fixture()
def selenium_login(app, selenium):
    yield _do_login(app.config["ADMIN_USER"], selenium)


@pytest.fixture()
def selenium_login_user(app, selenium):
    yield _do_login(app.config["USER"], selenium)


@pytest.fixture
def chrome_options(request, chrome_options):
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('w3c', False)
    chrome_options.set_capability('goog:loggingPrefs', { 'browser':'ALL' })
    chrome_options.add_argument('--window-size=1300,1000')
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
    with open(filename, "rb") as _file:
        _fakeUpload = FileStorage(
            stream=_file,
            filename="testdata.xlsx")
        result = import_xls(
            input_file=_fakeUpload,
            column_name=u'2018 Q4 (D)'
        )


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
    user_dict = app.config["USER_2"]
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
    for log_entry in extra:
        if log_entry["name"] == "Screenshot":
            content = base64.b64decode(log_entry["content"].encode("utf-8"))
            with open(os.path.join("tests", "{}.png".format(item.name)), "wb") as f:
                f.write(content)
        else:
            if log_entry["name"] == "Browser Log":
                print("Console:", log_entry["content"].encode("utf-8"))
