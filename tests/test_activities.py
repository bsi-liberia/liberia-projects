from flask import url_for


class TestActivities:
    def test_nonauth_routes_work(self, client):
        routes = [
            url_for('activities.export'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200

    def test_auth_routes_work(self, client, user):
        routes = [
            url_for('activities.dashboard'),
            url_for('activities.activities'),
            url_for('activities.activity_new'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200
