from projectdashboard.query import generate_csv as qgenerate_csv
from projectdashboard.lib import xlsx_to_csv, util, spreadsheet_headers
import re

def get_column_information(mtef, _headers):
    mtef_cols = list(filter(lambda col: re.match(r"(.*) \(MTEF\)", col), _headers))
    disb_cols = list(filter(lambda col: re.match(r"(.*) Q(.*) \(D\)", col), _headers))
    counterpart_funding_cols = list(filter(lambda col: re.match(r"(.*) \(GoL counterpart fund request\)", col), _headers))
    if mtef and _headers is None:
        mtef_cols = qgenerate_csv.mtef_fys()
        counterpart_funding_cols = qgenerate_csv.counterpart_fys()

        _headers = spreadsheet_headers.headers_disb_template_1
        _headers += counterpart_funding_cols
        _headers += mtef_cols
        _headers += spreadsheet_headers.headers_disb_template_2
        disb_cols = []
    elif _headers is None:
        mtef_cols = []
        counterpart_funding_cols = []
        disb_cols = [util.previous_fy_fq()]
        _headers = spreadsheet_headers.headers_mtef_template_1
        _headers += disb_cols
        _headers += spreadsheet_headers.headers_mtef_template_2
    return mtef_cols, counterpart_funding_cols, disb_cols, _headers
