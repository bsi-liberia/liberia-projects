from flask import url_for


class TestCodelists:
    def test_admin_routes_work(self, client, admin):
        routes = [
            url_for('codelists.codelists_management'),
        ]
        for route in routes:
            res = client.get(route)
            assert res.status_code == 200
