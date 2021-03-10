from flask import url_for
import json
import pytest

@pytest.mark.usefixtures('client_class')
class TestCodelists:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('codelists.codelists_management'), 401),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work(self, client, user, headers_user):
        routes = [
            (url_for('codelists.codelists_management'), 403),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_user)
            assert res.status_code == status_code

    def test_admin_routes_work(self, client, admin, headers_admin):
        routes = [
            (url_for('codelists.codelists_management'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_admin)
            assert res.status_code == status_code

    def test_admin_routes_work(self, client, admin, headers_admin):
        route = url_for('codelists.codelists_management')
        res = client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        assert len(data['codelist_codes']['mtef-sector']) == 12

class TestUpdateCodelists:
    def test_update_codelist(self, client, admin, headers_admin):
        route = url_for('codelists.codelists_management')
        res = client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        mtef_sector = data['codelist_codes']['mtef-sector'][1]
        assert mtef_sector['name'] == 'AGRICULTURE'

        # Update code name
        route = url_for('codelists.api_codelists_update')
        data = {
            'id': mtef_sector['id'],
            'codelist_code': 'mtef-sector',
            'attr': 'name',
            'value': 'AGRICULTURE-TEST'
        }
        res = client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200

        route = url_for('codelists.codelists_management')
        res = client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        mtef_sector_updated = data['codelist_codes']['mtef-sector'][1]
        assert mtef_sector_updated['name'] == 'AGRICULTURE-TEST'

        # Put code name back to how it was
        route = url_for('codelists.api_codelists_update')
        data = {
            'id': mtef_sector['id'],
            'codelist_code': 'mtef-sector',
            'attr': 'name',
            'value': 'AGRICULTURE'
        }
        res = client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200

    def test_add_delete_codelist(self, client, admin, headers_admin):
        # Create new code and add it
        route = url_for('codelists.api_codelists_new')
        data = {
            'codelist_code': 'mtef-sector',
            'code': '12345',
            'name': 'AGRICULTURE-NEW'
        }
        res = client.post(route, json=data, headers=headers_admin)
        new_code_id = json.loads(res.data)
        assert res.status_code == 200

        # Check there are now 13, rather than 12 codes
        route = url_for('codelists.codelists_management')
        res = client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        assert len(data['codelist_codes']['mtef-sector']) == 13

        # Delete new code
        route = url_for('codelists.api_codelists_delete')
        data = {
            'id': new_code_id,
            'codelist_code': 'mtef-sector'
        }
        res = client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200
