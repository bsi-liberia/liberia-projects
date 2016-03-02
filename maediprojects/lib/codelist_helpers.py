import json
import os

codelist_file = open(os.path.join(
    os.path.dirname(__file__), "codelist_helpers.json"
    ), 'r')
codelists_data = json.load(codelist_file)
def codelists(codelist_name):
    return codelists_data.get(codelist_name)