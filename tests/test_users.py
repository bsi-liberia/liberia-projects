from flask import url_for
import pytest

@pytest.mark.usefixtures('client_class')
class TestUsers:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('users.unauthenticated_user'), 200),
            (url_for('users.user'), 200),
            (url_for('users.users_new'), 401),
            (url_for('users.users_edit', user_id=1), 401),
            (url_for('users.user_permissions_edit', user_id=1), 401),
            (url_for('users.login'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, user, client):
        routes = [
            (url_for('users.unauthenticated_user'), 200),
            (url_for('users.user'), 200),
            (url_for('users.users_new'), 401),
            (url_for('users.users_edit', user_id=1), 401),
            (url_for('users.user_permissions_edit', user_id=1), 401),
            (url_for('users.login'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_admin_routes_work(self, admin, client, headers_admin):
        routes = [
            (url_for('users.unauthenticated_user'), 200),
            (url_for('users.user'), 200),
            (url_for('users.users_new'), 200),
            (url_for('users.users_edit', user_id=1), 200),
            (url_for('users.user_permissions_edit', user_id=1), 200),
            (url_for('users.login'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_admin)
            assert res.status_code == status_code
