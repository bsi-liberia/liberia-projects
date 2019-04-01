from flask import url_for


class TestDocumentation:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('documentation.help'), 302),
            (url_for('documentation.milestones'), 302),
            (url_for('documentation.disbursements_dashboard'), 302),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user):
        routes = [
            (url_for('documentation.help'), 200),
            (url_for('documentation.milestones'), 200),
            (url_for('documentation.disbursements_dashboard'), 200),
            (url_for('documentation.counterpart_funding'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code
