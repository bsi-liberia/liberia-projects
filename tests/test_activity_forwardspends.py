from flask import url_for
import pytest
import json


@pytest.mark.usefixtures('client_class')
class TestActivityFinances:
    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('activity_forwardspends.api_activity_forwardspends', activity_id=1), 403),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, admin, headers_admin):
        routes = [
            (url_for('activity_forwardspends.api_activity_forwardspends', activity_id=1), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code
            data = json.loads(res.data)
            assert len(data['forwardspends']) == 6
            assert data['forwardspends'][3]['year'] == 'FY2018'
            assert data['forwardspends'][3]['total_value'] == 1000.0
