from flask import url_for
import pytest
import json

@pytest.mark.usefixtures('client_class')
class TestManagement:
    def test_auth_routes_work_user(self, user):
        routes = [
            (url_for('activity_log.activity_log'), 401),
            (url_for('management.reporting_orgs'), 401)
        ]
        for route, status_code in routes:
            res = self.client.get(route)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, admin, headers_admin):
        routes = [
            (url_for('activity_log.activity_log'), 200),
            (url_for('management.reporting_orgs'), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code


    def test_reporting_orgs(self, admin, headers_admin):
        route = url_for('management.reporting_orgs')

        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        assert len(data.keys()) == 5
        assert len(data['orgs']) == 1

# TODO:
# - test adding or editing activities data leads to
#   changes in the activity log
# - test adding or editing activities data leads to
#   changes in the data quality table
