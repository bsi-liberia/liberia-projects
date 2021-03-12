from flask import url_for
import pytest
import json
from projectdashboard.query.activity import delete_activity

@pytest.mark.usefixtures('client_class')
class TestActivity:
    def test_auth_routes_work_admin(self, admin, headers_admin):
        routes = [
            (url_for('activities.api_new_activity', activity_id=1), 200)
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code


    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('activities.api_new_activity', activity_id=1), 403)
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


@pytest.mark.usefixtures('client_class')
class TestNewActivity:
    def test_new_activity_required_fields_fails_admin(self, admin, headers_admin):
        """
        Get data from new_activity and post back a new activity
        """
        route = url_for('activities.api_new_activity', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)["activity"]
        res_post = self.client.post(route,
            json=data,
            headers=headers_admin)
        assert res_post.status_code==400


    def test_new_activity(self, admin, headers_admin):
        """
        Get data from new_activity and post back a new activity
        """
        route = url_for('activities.api_new_activity')
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)["activity"]
        data['reporting_org_id'] = 1
        res_post = self.client.post(route,
            json=data,
            headers=headers_admin)
        assert res_post.status_code==200

        added_activity_data = json.loads(res_post.data)
        deleted = delete_activity(added_activity_data['id'])
        assert deleted == True


@pytest.mark.usefixtures('client_class')
class TestEditActivity:

    def test_edit_activity(self, admin, headers_admin):
        """
        Update the title for an activity, and then put it back.
        """
        # Update the title
        route = url_for('activities.activity_edit_attr', activity_id=1)
        postdata = {
            'attr': 'title',
            'value': 'New Title',
            'type': 'activity'
        }
        res = self.client.post(route, json=postdata, headers=headers_admin)

        # Check that it has been updated
        route = url_for('activities.api_activities_by_id', activity_id=1)
        res = self.client.get(route, headers=headers_admin)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['activity']['title'] == "New Title"

        # Put it back to how it was
        route = url_for('activities.activity_edit_attr', activity_id=1)
        postdata = {
            'attr': 'title',
            'value': 'Education project',
            'type': 'activity'
        }
        res = self.client.post(route, json=postdata, headers=headers_admin)

# TODO:
# - test changing various other fields (classifications, organisations)
# - test adding / deleting locations
