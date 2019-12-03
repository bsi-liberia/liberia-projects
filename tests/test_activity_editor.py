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
    assert selenium.find_element(By.TAG_NAME, 'html')
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'h1'))
    )
    assert selenium.find_element(field_selector, field_name).get_property("value") == original_value
    select = Select(selenium.find_element(field_selector, field_name))
    select.select_by_value(new_value)
    time.sleep(1)
    assert "is-valid" in selenium.find_element(field_selector,field_name).find_element(By.XPATH, "../..").get_attribute("class")
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'h1'))
    )
    assert selenium.find_element(field_selector, field_name).get_property("value") == new_value


def _test_text_field(self, app, selenium, selenium_login, field_selector, field_name, original_value, append_value):
    # self, app, selenium, selenium_login, By.TAG, "title", "Education project", " TEST"
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'h1'))
    )
    selenium.find_element(field_selector, field_name).send_keys(append_value)
    selenium.find_element(By.TAG_NAME, "h1").click()
    time.sleep(1)
    assert "is-valid" in selenium.find_element(field_selector, field_name).find_element(By.XPATH, "../..").get_attribute("class")
    selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'h1'))
    )
    assert selenium.find_element(field_selector, field_name).get_property("value") == "{}{}".format(original_value, append_value)


@pytest.mark.usefixtures('client_class')
class TestActivityEditor(LiveServerClass):
    def test_activity_editor_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=2, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
        assert selenium.find_element(By.TAG_NAME, "h1").text.startswith("Edit activity")

    def test_activity_editor_title(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
        assert selenium.find_element(By.NAME, "title").get_property("value") == "Education project"

    def test_activity_editor_title_edit(self, app, selenium, selenium_login):
        _test_text_field(self, app, selenium, selenium_login, By.NAME, "title", "Education project", " TEST")

    #def test_activity_editor_aid_type_edit(self, app, selenium, selenium_login):
    #    _test_select_field(self, app, selenium, selenium_login, By.NAME, "aid_type", "A01", "D01")

    #def test_activity_editor_reporting_org_edit(self, app, selenium, selenium_login):
    #    _test_select_field(self, app, selenium, selenium_login, By.NAME, "reporting_org_id", "1", "11")

    #def test_activity_editor_funding_org_edit(self, app, selenium, selenium_login):
    #    _test_select_field(self, app, selenium, selenium_login, By.CSS_SELECTOR, "#organisations fieldset:nth-child(1) select", "1", "2")

    #def test_activity_editor_implementing_org_edit(self, app, selenium, selenium_login):
    #    _test_select_field(self, app, selenium, selenium_login, By.CSS_SELECTOR, ".organisations fieldset:nth-child(2) select", "2", "3")


@pytest.mark.usefixtures('client_class')
class TestActivityEditorLocations(LiveServerClass):
    def test_activity_locations(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=2, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.card-header ul.nav-tabs li.nav-item a[href="#/locations"]'))
        )
        selenium.find_element(By.CSS_SELECTOR, '.card-header ul.nav-tabs li.nav-item a[href="#/locations"]').click()
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#locationSelector div.btn-group-toggle label'))
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, "#locationSelector div.btn-group-toggle label")) > 1

    def test_add_activity_location(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=2, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.card-header ul.nav-tabs li.nav-item a[href="#/locations"]'))
        )
        selenium.find_element(By.CSS_SELECTOR, '.card-header ul.nav-tabs li.nav-item a[href="#/locations"]').click()
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#locationSelector div.btn-group-toggle label"))
        )
        # Click on the first element in the location selector
        selenium.find_element(By.CSS_SELECTOR, "#locationSelector div.btn-group-toggle label").click()
        time.sleep(2)
        # Check it was shown to be active, and that the location map has one marker now
        assert "active" in selenium.find_element(By.CSS_SELECTOR, "#locationSelector div.btn-group-toggle label").get_attribute("class")
        assert len(selenium.find_elements(By.CSS_SELECTOR, "#location-container .leaflet-marker-pane img")) == 1
