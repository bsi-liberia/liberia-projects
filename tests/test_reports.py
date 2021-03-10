from flask import url_for
import pytest

@pytest.mark.usefixtures('client_class')
class TestDocumentation:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('reports.project_development_tracking'), 401),
            (url_for('reports.aid_disbursements_api'), 200),
            (url_for('reports.psip_disbursements_api'), 401),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user, headers_user):
        routes = [
            (url_for('reports.project_development_tracking'), 200),
            (url_for('reports.aid_disbursements_api'), 200),
            (url_for('reports.psip_disbursements_api'), 200),
            (url_for('reports.counterpart_funding'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_user)
            assert res.status_code == status_code
