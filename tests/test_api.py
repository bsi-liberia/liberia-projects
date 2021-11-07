import json

from flask import url_for
import pytest

@pytest.mark.usefixtures('client_class')
class TestAPI:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('activities.api_activities_country'), 200),
            (url_for('iati.api_list_iati_files'), 200),
            (url_for('api.api_sectors'), 200),
            (url_for('api.api_sectors_C_D'), 200),
            (url_for('activity_locations.api_all_activity_locations'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work_user(self, client, user, headers_user):
        routes = [
            (url_for('activity_locations.api_all_activity_locations'), 200),
            (url_for('activities.api_activities_country'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_user)
            assert res.status_code == status_code

    def test_auth_routes_work_admin(self, client, admin, headers_admin):
        routes = [
            (url_for('activity_locations.api_all_activity_locations'), 200),
            (url_for('activities.api_activities_country'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_admin)
            assert res.status_code == status_code

    def test_aggregations_api(self, client, user, headers_user):
        route = url_for('api.api_aggregates',
            dimension='reporting-org',
            filter='mtef-sector',
            filter_value='07')
        res = client.get(route)
        data = json.loads(res.data)
        data_by_fy = dict([(entry['fy'], entry) for entry in data['entries']])

        assert data_by_fy['FY2018']['Disbursements'] == 0.0
        assert data_by_fy['FY2018']['Disbursement Projection'] == 11000.0
        assert data_by_fy['FY2019']['Disbursements'] == 200.0
        assert data_by_fy['FY2019']['Disbursement Projection'] == 0.0

    def test_aggregations_api(self, client, user, headers_user):
        route = url_for('api.api_aggregates',
            dimension='mtef-sector')
        res = client.get(route)
        data = json.loads(res.data)
        data_by_fy = dict([(entry['fy'], entry) for entry in data['entries']])

        assert data_by_fy['FY2018']['Disbursements'] == 0.0
        assert data_by_fy['FY2018']['Disbursement Projection'] == 29000.0
        assert data_by_fy['FY2019']['Disbursements'] == 5500.0
        assert data_by_fy['FY2019']['Disbursement Projection'] == 0.0
