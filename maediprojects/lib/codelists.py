import unicodecsv
import os

import flask_babel as babel

from maediprojects import models


def get_db_codelist_names():
    codelists = models.Codelist.query.all()
    return codelists

def get_db_codelists():
    # Get codelist name
    codelist_data = models.CodelistCode.query.order_by(
        models.CodelistCode.name
    ).all()
    codelists = dict(map(lambda k: (k.codelist_code, []), codelist_data))
    for cd in codelist_data:
        codelists[cd.codelist_code].append({
            "id": getattr(cd, "id", None),
            "code": cd.code,
            "name": cd.name
        })
    currencies = models.Currency.query.order_by(models.Currency.code).all()
    codelists["currency"] = [{
        'code': 'USD', 'id': 'USD', 'name': 'USD - U.S. Dollar'
        }]
    codelists["currency"] += (list(map(lambda currency: {
        'code': currency.code, 'id': currency.code,
        'name': '{} - {}'.format(currency.code, currency.name)
    }, currencies)))
    return codelists

def get_codelists(LANG=None):
    if not LANG:
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
            out[cl_name].append({"code": row["code"],
                "id": row.get("id", row.get("code")),
                "name": row["name_%s" % LANG]})
    out.update(get_db_codelists())
    out['domestic_external'] = [
        {'code': 'domestic', 'id': 'domestic', 'name': 'Domestic / PSIP (PIU)'},
        {'code': 'external', 'id': 'external', 'name': 'External / Aid (AMCU)'}]
    return out

def get_codelists_lookups():
    codelists = {}
    in_codelists = get_codelists()
    for cl, cl_items in in_codelists.items():
        codelists[cl] = {}
        for cl_item in cl_items:
            codelists[cl][cl_item["code"]] = cl_item["name"]
    return codelists

def get_codelists_lookups_by_code():
    codelists = {}
    in_codelists = get_codelists()
    for cl, cl_items in in_codelists.items():
        codelists[cl] = {}
        for cl_item in cl_items:
            codelists[cl][cl_item["code"]] = cl_item["id"]
    return codelists

def get_codelists_lookups_by_name():
    codelists = {}
    in_codelists = get_codelists()
    for cl, cl_items in in_codelists.items():
        codelists[cl] = {}
        for cl_item in cl_items:
            codelists[cl][cl_item["name"]] = cl_item["code"]
    return codelists

def get_codelists_ids_by_name():
    codelists = {}
    in_codelists = get_codelists()
    for cl, cl_items in in_codelists.items():
        codelists[cl] = {}
        for cl_item in cl_items:
            codelists[cl][cl_item["name"]] = cl_item.get("id",
                cl_item.get("code"))
    return codelists
