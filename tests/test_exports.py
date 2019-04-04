from flask import url_for


class TestAPI:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('exports.activities_csv'), 200),
            (url_for('exports.activities_xlsx_transactions'), 200),
            (url_for('exports.activities_xlsx'), 200),
            (url_for('exports.all_activities_xlsx'), 200),
            (url_for('exports.all_activities_xlsx_filtered'), 200),
            (url_for('exports.export'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user):
        routes = [
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
