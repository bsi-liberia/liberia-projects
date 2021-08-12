from flask import url_for
import pytest
import re
from io import StringIO, BytesIO
from projectdashboard.views.api import JSONEncoder
from projectdashboard.lib.xlsx_to_csv import getDataFromFile
from projectdashboard.query import organisations as qorganisations
import csv
import json
import openpyxl


@pytest.mark.usefixtures('client_class')
class TestImportFiles:

    def test_import_disbursements_xlsx_file(self, client, admin, headers_admin):
        route_activity = url_for('activity_finances.api_activity_finances', activity_id=1)
        res_activity1 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity1.data)
        assert len(data['finances']['disbursements']) == 1

        route = url_for('exports.import_template')
        data = {
            'file': (open('tests/artefacts/api/exports/import_template_disbursements.xlsx', 'rb'), 'disbursements.xlsx'),
            'template_type': 'disbursements',
            'fy_fq': 'FY2019 Q2 (D)'
        }
        res = client.post(route, data=data, headers=headers_admin)
        data = json.loads(res.data)

        res_activity2 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity2.data)
        assert len(data['finances']['disbursements']) == 2


    def test_import_mtef_xlsx_file(self, client, admin, headers_admin):
        route_activity = url_for('activity_forwardspends.api_activity_forwardspends', activity_id=1)
        res_activity1 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity1.data)
        assert data['forwardspends'][6]['year'] == 'FY2021'
        assert data['forwardspends'][6]['total_value'] == 0

        route = url_for('exports.import_template')
        data = {
            'file': (open('tests/artefacts/api/exports/import_template_mtef.xlsx', 'rb'), 'mtef.xlsx'),
            'template_type': 'mtef'
        }
        res = client.post(route, data=data, headers=headers_admin)
        data = json.loads(res.data)

        res_activity2 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity2.data)
        assert data['forwardspends'][6]['year'] == 'FY2021'
        assert data['forwardspends'][6]['total_value'] == 500.0


    def test_import_psip_xlsx_file(self, client, admin, headers_admin):
        route_activity = url_for('activity_finances.api_activity_finances', activity_id=11)
        res_activity1 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity1.data)
        assert len(data['finances']['disbursements']) == 0

        route = url_for('exports.import_psip_transactions')
        data = {
            'file': (open('tests/artefacts/api/exports/import_psip_transactions.xlsx', 'rb'), 'psip.xlsx'),
            'fiscal_year': 'FY2019'
        }
        res = client.post(route, data=data, headers=headers_admin)
        data = json.loads(res.data)

        res_activity2 = self.client.get(route_activity, headers=headers_admin)
        data = json.loads(res_activity2.data)
        assert len(data['finances']['disbursements']) == 1
        assert data['finances']['disbursements'][0]['transaction_value'] == 1500.0
        assert data['finances']['disbursements'][0]['transaction_date'] == '2019-07-31'
