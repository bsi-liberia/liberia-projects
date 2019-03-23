from flask import url_for


class TestUsers:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('users.login'), 200),
            (url_for('users.profile'), 302),
            (url_for('users.users'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, user, client):
        routes = [
            (url_for('users.profile'), 200),
            (url_for('users.users'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_admin_routes_work(self, admin, client):
        routes = [
            (url_for('users.users'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
