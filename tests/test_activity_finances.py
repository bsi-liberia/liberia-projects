from flask import url_for
import pytest
import json


@pytest.mark.usefixtures('client_class')
class TestActivityFinances:
    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('activity_finances.api_activity_finances', activity_id=1), 403),
            (url_for('activity_finances.api_activity_finances', activity_id=2), 403),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, admin, headers_admin):
        routes = [
            (url_for('activity_finances.api_activity_finances', activity_id=1), 200),
            (url_for('activity_finances.api_activity_finances', activity_id=2), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code
            data = json.loads(res.data)
            assert len(data["finances"]) == 3
            assert len(data["finances"]['disbursements']) == 1


    def test_edit_finances(self, admin, headers_admin):
        activity_id = 1
        # Check transaction value is 100.00
        route = url_for('activity_finances.api_activity_finances', activity_id=activity_id)
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)["finances"]
        disbursement = data['disbursements'][0]
        assert disbursement['transaction_value_original'] == 100.00

        # Change it too 500.00
        route = url_for('activity_finances.finances_edit_attr', activity_id=activity_id)
        data = {
            'activity_id': activity_id,
            'attr': 'transaction_value_original',
            'value': 500.00,
            'finances_id': disbursement['id']
        }
        res = self.client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200
        assert json.loads(res.data)['transaction_value_original'] == 500.00
        # We make sure that the USD value has been automatically updated to reflect this
        assert json.loads(res.data)['transaction_value'] == 500.00

        # Change it back to 100.00
        data = {
            'activity_id': activity_id,
            'attr': 'transaction_value_original',
            'value': 100.00,
            'finances_id': disbursement['id']
        }
        res = self.client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200


    def test_add_delete_finances(self, admin, headers_admin):
        activity_id = 1
        # Check there is only 1 disbursement
        route = url_for('activity_finances.api_activity_finances', activity_id=activity_id)
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)["finances"]
        assert len(data['disbursements']) == 1

        # Add one disbursement of USD 200
        data = {
            'transaction_type': 'D',
            'transaction_date': '2020-12-31',
            'transaction_value_original': 200.00,
            'currency': 'USD',
            'action': 'add',
            'fund_source_id': None
        }
        res = self.client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200
        transaction = json.loads(res.data)
        assert transaction['transaction_value_original'] == 200.00

        # Check there are now two disbursements
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)["finances"]
        assert len(data['disbursements']) == 2

        # Delete transaction
        data = {
            'action': 'delete',
            'activity_id': activity_id,
            'transaction_id': transaction['id']
        }
        res = self.client.post(route, json=data, headers=headers_admin)
        assert res.status_code == 200
