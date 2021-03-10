from flask import url_for
import pytest
import warnings
import json


@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('activities.api_activities_by_id', activity_id=1), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, user, headers_admin):
        routes = [
            (url_for('activities.api_activities_by_id', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code


    def test_finance_auth_routes_work_admin(self, user, headers_admin):
        route = url_for('activity_finances.api_activity_finances', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert len(data["finances"]) > 0


    def test_first_project_title_correct(self, user, headers_user):
        route = url_for('activities.api_activities_by_id', activity_id=1)
        res = self.client.get(route, headers=headers_user)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['activity']['title'] == "Education project"


    def test_first_project_finances_correct(self, user, headers_admin):
        route = url_for('activity_finances.api_activity_finances', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert len(data["finances"]['disbursements'])>0
