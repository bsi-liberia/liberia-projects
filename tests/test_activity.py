from flask import url_for
import pytest
import warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work(self, user):
        routes = [
            (url_for('activities.activity', activity_id=1), 200),
            (url_for('activities.activity_edit', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


@pytest.mark.usefixtures('live_server')
@pytest.mark.usefixtures('client_class')
class TestActivityLoads():
    def test_activity_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity', activity_id=1, _external=True))
        WebDriverWait(selenium, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
        assert selenium.find_element(By.TAG_NAME, "h1").text == "Education project"

    def test_activity_editor_loads(self, app, selenium, selenium_login):
        selenium.get(url_for('activities.activity_edit', activity_id=2, _external=True))
        WebDriverWait(selenium, 5).until(
            EC.presence_of_element_located((By.ID, 'financesTab'))
        )
        assert selenium.find_element(By.TAG_NAME, "h1").text.startswith("Edit activity")