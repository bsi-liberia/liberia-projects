from flask import url_for
import pytest
import warnings
import json


@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('activities.api_activities_by_id', activity_id=1), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, user, headers_admin):
        routes = [
            (url_for('activities.api_activities_by_id', activity_id=1), 200),
            (url_for('activities.api_activities_finances_fund_sources_by_id', activity_id=1), 200),
            (url_for('activity_finances.api_activity_finances', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code


    def test_api_activity_finances(self, user, headers_admin):
        route = url_for('activity_finances.api_activity_finances', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert len(data['finances']) == 3
        assert len(data['finances']['disbursements']) == 1
        #with open('tests/artefacts/api/activity_finances/api_activity_finances.json', 'w') as jsonfile:
        #    json.dump(data, jsonfile)
        with open('tests/artefacts/api/activity_finances/api_activity_finances.json', 'r') as jsonfile:
            file_data = json.load(jsonfile)
        assert data == file_data


    def test_api_activity_fund_sources(self, user, headers_admin):
        route = url_for('activities.api_activities_finances_fund_sources_by_id', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert list(data['finances'].keys()) == ['disbursement', 'forwardspend']
        assert list(data['fund_sources'].keys()) == ['null']
        #with open('tests/artefacts/api/activities/api_activities_finances_fund_sources_by_id.json', 'w') as jsonfile:
        #    json.dump(data, jsonfile)
        with open('tests/artefacts/api/activities/api_activities_finances_fund_sources_by_id.json', 'r') as jsonfile:
            file_data = json.load(jsonfile)
        assert data == file_data


    def test_first_project_title_correct(self, user, headers_user):
        route = url_for('activities.api_activities_by_id', activity_id=1)
        res = self.client.get(route, headers=headers_user)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['activity']['title'] == "Education project"


    def test_first_project_finances_correct(self, user, headers_admin):
        route = url_for('activity_finances.api_activity_finances', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert len(data["finances"]['disbursements'])>0
