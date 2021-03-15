from flask import url_for
import pytest
import warnings
import json
from projectdashboard.lib.xlsx_to_csv import getDataFromFile
from projectdashboard.views.api import JSONEncoder
from io import StringIO


def xlsx_to_csv_jsonfile(jsonfile):
    fn = 'tests/artefacts/testdata.xlsx'
    with open(fn, 'rb') as xlsxfile:
        data = getDataFromFile(fn, xlsxfile.read(), 'Sheet1')
    json.dump(data, jsonfile, cls=JSONEncoder)


def write_xlsx_to_csv_json():
    with open('tests/artefacts/lib/xlsx_to_csv.json', 'w') as jsonfile:
        xlsx_to_csv_jsonfile(jsonfile)


class TestXLSXtoCSV:
    def test_xlsx_csv(self):
        #write_xlsx_to_csv_json()
        jsonfile = StringIO()
        xlsx_to_csv_jsonfile(jsonfile)
        jsonfile.seek(0)
        with open('tests/artefacts/lib/xlsx_to_csv.json', 'r') as in_jsonfile:
            assert jsonfile.read() == in_jsonfile.read()
