from flask import url_for


class TestActivities:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('activities.export'), 200),
            (url_for('activities.dashboard'), 302),
            (url_for('activities.activities'), 302),
            (url_for('activities.activity_new'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user):
        routes = [
            (url_for('activities.dashboard'), 200),
            (url_for('activities.activities'), 200),
            (url_for('activities.activity_new'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
