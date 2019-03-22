from flask import url_for


class TestUsers:
    def test_nonauth_routes_work(self, client):
        routes = [
            url_for('users.login'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200

    def test_auth_routes_work(self, user, client):
        routes = [
            url_for('users.profile'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200

    def test_admin_routes_work(self, admin, client):
        routes = [
            url_for('users.users'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200
