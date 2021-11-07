from flask import url_for
import pytest
import warnings
import time
import json

@pytest.mark.usefixtures('client_class')
class TestActivities:
    def test_nonauth_routes_work(self):
        routes = [
            (url_for('activities.api_activities_filters'), 200),
            (url_for('activities.api_activities_country'), 200),
            (url_for('activities.api_new_activity'), 401),
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_user(self, user):
        routes = [
            (url_for('activities.api_activities_filters'), 200),
            (url_for('activities.api_activities_country'), 200),
            (url_for('activities.api_new_activity'), 401),
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, admin, headers_admin):
        routes = [
            (url_for('activities.api_activities_filters'), 200),
            (url_for('activities.api_activities_country'), 200),
            (url_for('activities.api_new_activity'), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code


    def test_activities_api_works(self, admin, headers_admin):
        res = self.client.get(url_for('activities.api_activities_country'),
            headers=headers_admin)
        assert res.status_code == 200
        assert len(json.loads(res.data)["activities"]) == 11


    def test_filters_api_works(self, admin, app):
        res = self.client.get(url_for('activities.api_activities_filters'))
        assert res.status_code == 200
        assert len(json.loads(res.data)["filters"]) == 10
