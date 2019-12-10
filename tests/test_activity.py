from flask import url_for
import pytest
import warnings
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from conftest import LiveServerClass

@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work_user(self, user):
        routes = [
            (url_for('activities.activity', activity_id=1), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, user):
        routes = [
            (url_for('activities.activity', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_finance_auth_routes_work_admin(self, user):
        route = url_for('api.api_activities_finances_by_id', activity_id=1)
        res = self.client.get(route)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert len(data["finances"]) > 0


@pytest.mark.usefixtures('client_class')
class TestActivityLoads(LiveServerClass):
    def test_activity_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
        assert selenium.find_element(By.TAG_NAME, "h1").text == "Education project"

    def test_activity_transactions_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#disbursement-table tbody tr'))
        )
        assert selenium.find_element(By.CSS_SELECTOR, "#disbursement-table tbody tr td:nth-child(2)"
            ).text == "100.00"
