from flask import url_for
import pytest
import re
from io import StringIO, BytesIO
from projectdashboard.views.api import JSONEncoder
from projectdashboard.lib.xlsx_to_csv import getDataFromFile
import csv
import json

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


def write_csv_file(res):
    with open('tests/artefacts/api/exports/activities_csv.csv', 'w') as csvfile:
        remove_last_updated_date(res, csvfile)


def read_csv_file_from_request(res):
    writer = StringIO()
    remove_last_updated_date(res, writer)
    writer.seek(0)
    return writer.read()


def remove_last_updated_date(res, csvfile):
    res_csv_f = StringIO(res.get_data(as_text=True))
    csvreader = csv.DictReader(res_csv_f)
    fieldnames = [fieldname for fieldname in csvreader.fieldnames if fieldname != 'Last updated date']
    csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csvwriter.writeheader()
    for row in csvreader:
        csvwriter.writerow(excl_last_updated(row))


def excl_last_updated(row):
    row.pop('Last updated date')
    return row


def get_clean_data_from_file(xlsx_filename, sheetname='Sheet1'):
    if type(xlsx_filename) == BytesIO:
        data = getDataFromFile(xlsx_filename, xlsx_filename.read(), sheetname)
    else:
        with open(xlsx_filename, 'rb') as xlsxfile:
            data = getDataFromFile(xlsx_filename, xlsxfile.read(), sheetname)
    return list(map(lambda row: excl_last_updated(row), data))


@pytest.mark.usefixtures('client_class')
class TestExportFiles:
    def test_activities_csv(self, client):
        route = url_for('exports.activities_csv')
        res = client.get(route)

        # NB https://docs.python.org/3/library/csv.html#csv.Dialect.lineterminator
        # write_csv_file(res)

        with open('tests/artefacts/api/exports/activities_csv.csv', 'r') as csvfile:
            in_csv = re.sub("\r\n", "\n", read_csv_file_from_request(res))
            assert in_csv == csvfile.read()

    def test_exports_xlsx(self, client):
        route = url_for('exports.activities_xlsx', domestic_external="external")
        res = client.get(route)
        xlsx_file = BytesIO(res.get_data())
        xlsx_file_as_json = getDataFromFile(xlsx_file, xlsx_file.read(), 'Data1')
        assert len(xlsx_file_as_json) == 10

    def test_exports_xlsx(self, client):
        route = url_for('exports.activities_xlsx', domestic_external="external")
        res = client.get(route)
        #with open('tests/artefacts/api/exports/activities_xlsx.xlsx', 'wb') as f:
        #    f.write(res.get_data())

        xlsx_saved = get_clean_data_from_file('tests/artefacts/api/exports/activities_xlsx.xlsx', 'Data1')

        f = BytesIO(res.get_data())
        xlsx_res = get_clean_data_from_file(f, 'Data1')

        assert xlsx_res == xlsx_saved
