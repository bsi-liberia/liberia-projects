from flask import url_for
import pytest
import json
import dateutil.parser


@pytest.mark.usefixtures('client_class')
class TestFiscalYears:
    def test_auth_routes_work_user(self, user, headers_user):
        routes = [
            (url_for('admin.api_fiscal_year_choices'), 403),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_user)
            assert res.status_code == status_code


    def test_auth_routes_work_admin(self, app, admin, headers_admin):
        routes = [
            (url_for('admin.api_fiscal_year_choices'), 200),
        ]
        for route, status_code in routes:
            res = self.client.get(route, headers=headers_admin)
            assert res.status_code == status_code
            data = json.loads(res.data)
            assert data["earliestDate"] == app.config['FY_EARLIEST_DATE'].isoformat()
            assert data["latestDate"] == app.config['LATEST_DATE'].isoformat()


    def test_repost_fiscal_years(self, admin, headers_admin):
        """
        Repost fiscal years data back to the same API
        """
        route = url_for('admin.api_fiscal_year_choices')
        res = self.client.get(route, headers=headers_admin)
        data = json.loads(res.data)
        def fix_fyc(fyc):
            return {
                'start_date': dateutil.parser.parse(fyc['start_date']).date().isoformat(),
                'end_date': dateutil.parser.parse(fyc['end_date']).date().isoformat()
            }
        fiscal_year_choices = list(map(lambda fyc: fix_fyc(fyc), data['fiscalYearChoices']))
        res_post = self.client.post(route, headers=headers_admin, json=fiscal_year_choices)
        assert res_post.status_code == 200


    def test_update_fiscal_years(self, app, admin, headers_admin):
        """
        Change fiscal years to shift to a July-June FY and back again
        """
        route = url_for('admin.api_fiscal_year_choices')
        route_finances = url_for('activities.api_activities_finances_by_id', activity_id=1)

        # Check FY is FY2019
        res_finances = self.client.get(route_finances, headers=headers_admin)
        data_finances = json.loads(res_finances.data)
        assert data_finances['finances']['disbursement']['data'][0]['fiscal_year'] == "FY2019"

        # Update FYs with breaks
        fiscal_year_choices = [
            {
                'start_date': '2013-01-01',
                'end_date': '2013-12-31'
            },
            {
                'start_date': '2014-01-01',
                'end_date': '2014-06-30'
            },
            {
                'start_date': '2014-07-01',
                'end_date': '2040-06-30'
            },
            {
                'start_date': '2040-07-01',
                'end_date': '2040-12-31'
            },
            {
                'start_date': '2041-01-01',
                'end_date': '2049-12-31'
            },
        ]
        res_post = self.client.post(route, headers=headers_admin, json=fiscal_year_choices)
        assert res_post.status_code == 200

        # Check FY is FY2018/2019
        res_finances = self.client.get(route_finances, headers=headers_admin)
        data_finances = json.loads(res_finances.data)
        assert data_finances['finances']['disbursement']['data'][0]['fiscal_year'] == "FY2018/2019"

        # Update FYs without breaks
        fiscal_year_choices = [
            {
                'start_date': app.config['EARLIEST_DATE'].isoformat(),
                'end_date': app.config['LATEST_DATE'].isoformat()
            }
        ]
        res_post = self.client.post(route, headers=headers_admin, json=fiscal_year_choices)
        assert res_post.status_code == 200

        # Checek FY is FY2019
        res_finances = self.client.get(route_finances, headers=headers_admin)
        data_finances = json.loads(res_finances.data)
        assert data_finances['finances']['disbursement']['data'][0]['fiscal_year'] == "FY2019"
