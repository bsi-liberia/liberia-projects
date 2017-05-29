# -*- coding: UTF-8 -*-

from maediprojects import app, db, models
import datetime
from maediprojects.query import activity as qactivity
from maediprojects.lib.spreadsheet_headers import headers, fr_headers
from maediprojects.lib.codelist_helpers import codelists 
from maediprojects.lib.codelists import get_codelists_lookups
from io import BytesIO
import re
from generate_csv import activity_to_json
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.writer.excel import save_virtual_workbook

def generate_xlsx():
    def guess_types(cell_value):
        try:
            if float(cell_value) == int(float(cell_value)):
                return int(float(cell_value))
            return float(cell_value)
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(cell_value, "%Y-%m-%d").date()
        except ValueError:
            pass
        return cell_value
    
    class xlsxDictWriter(object):
        def writerow(self, row_data):
            hm = self.header_mapping
            for column_header, cell in row_data.items():
                column_letter = get_column_letter((hm[column_header]))
                self.ws.cell('%s%s'%(column_letter, (self.row_index))
                    ).value = guess_types(cell)
            self.row_index += 1
        
        def writeheader(self):
            self.header_mapping.values()
            self.writerow(dict(map(
                lambda x: (x, x), self.header_mapping.keys()
            )))
        
        def save(self):
            out = BytesIO()
            self.wb.save(out)
            return out
        
        def __init__(self, headers):
            self.wb = Workbook()
            self.ws = self.wb.worksheets[0]
            self.row_index = 1
            self.header_mapping = dict(
                map(lambda x: (x[1], x[0]), enumerate(headers, start=1)))
    
    writer = xlsxDictWriter(headers)
    writer.writeheader()
    fr_headers_row = dict(map(lambda x: (x[1], fr_headers[x[0]]), enumerate(headers)))
    writer.writerow(fr_headers_row)
    cl_lookups = get_codelists_lookups()
    activities = qactivity.list_activities()
    for activity in activities:
        writer.writerow(activity_to_json(activity, cl_lookups))
    
    return writer.save()
