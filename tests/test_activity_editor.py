from flask import url_for
import pytest
import warnings
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from conftest import LiveServerClass

@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work_admin(self, admin):
        routes = [
            (url_for('activities.activity_edit', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_user(self, user):
        routes = [
            (url_for('activities.activity_edit', activity_id=1), 302)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


def _test_select_field(self, app, selenium, selenium_login, field_selector, field_name, original_value, new_value):
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, 'financesTab'))
    )
    assert selenium.find_element(field_selector, field_name).get_attribute("value") == original_value
    select = Select(selenium.find_element(field_selector, field_name))
    select.select_by_value(new_value)
    time.sleep(1)
    assert "success" in selenium.find_element(field_selector,field_name).find_element(By.XPATH, "../..").get_attribute("class")
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, 'financesTab'))
    )
    assert selenium.find_element(field_selector, field_name).get_attribute("value") == new_value


def _test_text_field(self, app, selenium, selenium_login, field_selector, field_name, original_value, append_value):
    # self, app, selenium, selenium_login, By.TAG, "title", "Education project", " TEST"
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, 'financesTab'))
    )
    selenium.find_element(field_selector, field_name).send_keys(append_value)
    selenium.find_element(By.TAG_NAME, "h1").click()
    time.sleep(1)
    assert "success" in selenium.find_element(field_selector, field_name).find_element(By.XPATH, "../..").get_attribute("class")
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, 'financesTab'))
    )
    assert selenium.find_element(field_selector, field_name).get_attribute("value") == "{}{}".format(original_value, append_value)


@pytest.mark.usefixtures('client_class')
class TestActivityLoads(LiveServerClass):

    def test_activity_editor_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=2, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'financesTab'))
        )
        assert selenium.find_element(By.TAG_NAME, "h1").text.startswith("Edit activity")

    def test_activity_editor_title(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'financesTab'))
        )
        assert selenium.find_element(By.NAME, "title").get_attribute("value") == "Education project"

    def test_activity_editor_title_edit(self, app, selenium, selenium_login):
        _test_text_field(self, app, selenium, selenium_login, By.NAME, "title", "Education project", " TEST")

    def test_activity_editor_aid_type_edit(self, app, selenium, selenium_login):
        _test_select_field(self, app, selenium, selenium_login, By.NAME, "aid_type", "A01", "D01")

    def test_activity_editor_reporting_org_edit(self, app, selenium, selenium_login):
        _test_select_field(self, app, selenium, selenium_login, By.NAME, "reporting_org_id", "1", "11")

    def test_activity_editor_funding_org_edit(self, app, selenium, selenium_login):
        _test_select_field(self, app, selenium, selenium_login, By.CSS_SELECTOR, ".organisations div:nth-child(1) select", "1", "2")

    def test_activity_editor_implementing_org_edit(self, app, selenium, selenium_login):
        _test_select_field(self, app, selenium, selenium_login, By.CSS_SELECTOR, ".organisations div:nth-child(2) select", "1", "3")
