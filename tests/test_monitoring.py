from flask import url_for
import pytest
import warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json
import time
from conftest import LiveServerClass
import test_activity_finances

@pytest.mark.usefixtures('client_class')
class TestActivityLog:
    def test_auth_routes_work_user(self, user):
        routes = [
            (url_for('api.activity_log'), 302),
            (url_for('api.reporting_orgs'), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, admin):
        routes = [
            (url_for('api.activity_log'), 200),
            (url_for('api.reporting_orgs'), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


@pytest.mark.usefixtures('client_class')
class TestActivityLogLoads(LiveServerClass):

    def test_activity_log_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('users.users_log', _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#usersLog tbody tr'))
        )
        original_num_entries = len(selenium.find_elements(By.CSS_SELECTOR, '#usersLog tbody tr'))
        test_activity_finances.add_activity_finances(self, app, selenium, selenium_login)
        time.sleep(1)
        selenium.get(url_for('users.users_log', _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#usersLog tbody tr'))
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, '#usersLog tbody tr')) > original_num_entries

    def test_activity_log_popup_loads(self, app, selenium, selenium_login):
        test_activity_finances.add_activity_finances(self, app, selenium, selenium_login)
        selenium.get(url_for('users.users_log', _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#usersLog tbody tr'))
        )
        time.sleep(1)
        selenium.find_element(By.CSS_SELECTOR, '#usersLog tbody tr td:nth-child(5) a').click()
        time.sleep(1) # Wait one second for DB roundtrip
        assert("Activity" in selenium.find_element(By.CSS_SELECTOR, "#activityLogDetail header h5").text)


@pytest.mark.usefixtures('client_class')
class TestDataQualityLoads(LiveServerClass):

    def test_data_quality_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('management.dataquality', _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#reportingOrgs tbody tr'))
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, '#reportingOrgs tbody tr')) == 1

    def test_data_quality_correct(self, app, selenium, selenium_login):
        selenium.get(url_for('management.dataquality', _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#reportingOrgs tbody tr'))
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, '#reportingOrgs tbody tr td i.fa.fa-check-circle.text-success')) > 0

