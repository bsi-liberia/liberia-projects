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

@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work(self, user):
        routes = [
            (url_for('api.api_activity_finances', activity_id=1), 200),
            (url_for('api.api_activity_finances', activity_id=2), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code
            assert len(json.loads(res.data)["finances"]) == 1


@pytest.mark.usefixtures('client_class')
class TestActivityLoads(LiveServerClass):

    def test_activity_editor_finances_tab(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'financesTab'))
        )
        selenium.find_element(By.ID, "financesTab").click()
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#financial-data-D table tbody tr'))
        )
        assert selenium.find_element(By.CSS_SELECTOR, "#financial-data-D table tbody tr"
            ).find_element(By.NAME, "transaction_value"
            ).get_attribute("value") == "100.00"

    def test_add_activity_finances(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=1, _external=True))
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'financesTab'))
        )
        selenium.find_element(By.ID, "financesTab").click()
        selenium.find_element(By.CSS_SELECTOR, "#collapseDisbursements .addFinancial").click()
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#financial-data-D table tbody tr:nth-child(2)'))
        )
        assert len(selenium.find_elements(By.CSS_SELECTOR, "#financial-data-D table tbody tr")) == 2
        newrow = selenium.find_element(By.CSS_SELECTOR, "#financial-data-D table tbody tr:nth-child(2)")
        newrow.find_element(By.NAME, "transaction_value_original").send_keys(Keys.BACKSPACE)
        newrow.find_element(By.NAME, "transaction_value_original").send_keys("500.00")
        newrow.find_element(By.NAME, "transaction_description").click()
        time.sleep(1) # Wait one second for DB roundtrip
        assert("success" in newrow.find_element(By.NAME, "transaction_value_original").find_element(By.XPATH, "..").find_element(By.XPATH, "..").get_attribute("class"))
