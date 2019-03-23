from flask import url_for


class TestCodelists:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('codelists.codelists_management'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user):
        routes = [
            (url_for('codelists.codelists_management'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_admin_routes_work(self, client, admin):
        routes = [
            (url_for('codelists.codelists_management'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
