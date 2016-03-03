import unicodecsv
import os
from maediprojects import app, db, models
import flask.ext.babel as babel

def get_db_codelist_names():
    codelists = models.Codelist.query.all()
    return codelists

def get_db_codelists():
    # Get codelist name
    # { codelist: cdata }
    codelist_data = models.CodelistCode.query.all()
    codelists = dict(map(lambda k: (k.codelist_code, []), codelist_data))
    for cd in codelist_data:
        codelists[cd.codelist_code].append({
            "code": cd.code,
            "name": cd.name
        })
    return codelists

def get_codelists():
    LANG = babel.get_locale()
    current_dir = os.path.join(os.path.dirname(__file__))
    
    def only_csv(filename):
        if filename.endswith(".csv"): return True
        return False
    
    codelists = filter(only_csv, os.listdir(os.path.join(current_dir, "data")))
    out = {}
    for codelist in codelists:
        cl_name = codelist.split(".")[0]
        out[cl_name] = []
        cl_file = open(os.path.join(current_dir, "data", codelist), "r")
        csv = unicodecsv.DictReader(cl_file)
        for row in csv:
            out[cl_name].append({"code": row["code"], "name": row["name_%s" % LANG]})
    out.update(get_db_codelists())
    return out

def get_codelists_lookups():
    codelists = {}
    in_codelists = get_codelists()
    for cl, cl_items in in_codelists.items():
        codelists[cl] = {}
        for cl_item in cl_items:
            codelists[cl][cl_item["code"]] = cl_item["name"]
    return codelists
