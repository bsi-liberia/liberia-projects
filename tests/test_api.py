from flask import url_for


class TestAPI:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('api.api_activities_country'), 302),
            (url_for('api.api_list_routes'), 200),
            (url_for('api.api_list_iati_files'), 200),
            (url_for('api.api_sectors'), 200),
            (url_for('api.api_sectors_C_D'), 200),
            (url_for('api.api_all_activity_locations'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work_user(self, client, user):
        routes = [
            (url_for('api.api_all_activity_locations'), 200),
            (url_for('api.api_activities_country'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work_admin(self, client, admin):
        routes = [
            (url_for('api.api_all_activity_locations'), 200),
            (url_for('api.api_activities_country'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
