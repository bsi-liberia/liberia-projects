from flask import url_for


class TestAPI:
    def test_nonauth_routes_work(self, client):
        routes = [
            url_for('api.api_activities_country'),
            url_for('api.api_list_routes'),
            url_for('api.api_list_iati_files'),
            # url_for('api.api_iati_search'),
            url_for('api.api_sectors'),
            url_for('api.api_sectors_C_D'),
            url_for('api.activities_csv'),
            # url_for('api.activities_xlsx_transactions'),
            # url_for('api.activities_xlsx'),
            url_for('api.all_activities_xlsx'),
            url_for('api.all_activities_xlsx_filtered'),
            # url_for('api.export_donor_template'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200

    def test_auth_routes_work(self, client, user):
        routes = [
            url_for('api.api_all_activity_locations'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200
