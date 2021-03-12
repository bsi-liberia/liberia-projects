from flask import url_for
import pytest
import re

@pytest.mark.usefixtures('client_class')
class TestExports:
    def test_nonauth_routes_work(self, client):
        routes = [
            (url_for('exports.activities_csv'), 200),
            (url_for('exports.activities_xlsx_transactions'), 200),
            (url_for('exports.activities_xlsx', domestic_external="external"), 200),
            (url_for('exports.all_activities_xlsx'), 200),
            (url_for('exports.all_activities_xlsx_filtered'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route)
            assert res.status_code == status_code

    def test_auth_routes_work_user(self, client, user, headers_user):
        routes = [
            (url_for('exports.activities_csv'), 200),
            (url_for('exports.activities_xlsx_transactions'), 200),
            (url_for('exports.activities_xlsx', domestic_external="external"), 200),
            (url_for('exports.all_activities_xlsx'), 200),
            (url_for('exports.all_activities_xlsx_filtered'), 200),
        ]
        for route, status_code in routes:
            res = client.get(route, headers=headers_user)
            assert res.status_code == status_code


@pytest.mark.usefixtures('client_class')
class TestExportFiles:
    def test_activities_csv(self, client):
        route = url_for('exports.activities_csv')
        res = client.get(route)
        # NB https://docs.python.org/3/library/csv.html#csv.Dialect.lineterminator
        with open('tests/artefacts/exports/exports.activities_csv.csv', 'r') as csvfile:
            in_csv = re.sub("\r\n", "\n", res.data.decode("utf-8"))
            assert in_csv == csvfile.read()
