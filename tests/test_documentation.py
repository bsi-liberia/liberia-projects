from flask import url_for


class TestDocumentation:
    def test_auth_routes_work(self, client, user):
        routes = [
            url_for('documentation.help'),
            url_for('documentation.milestones'),
            url_for('documentation.disbursements_dashboard'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200
