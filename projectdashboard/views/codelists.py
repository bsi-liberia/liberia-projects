from flask import Blueprint, flash, request, \
    redirect, url_for, jsonify
from flask_login import login_required, current_user

from projectdashboard.query import location as qlocation
from projectdashboard.query import organisations as qorganisations
from projectdashboard.query import codelists as qcodelists
from projectdashboard.query import user as quser
from projectdashboard.lib import codelists
from flask_jwt_extended import jwt_required


blueprint = Blueprint('codelists', __name__, url_prefix='/api/codelists')


@blueprint.route("/")
@jwt_required()
@quser.administrator_required
def codelists_management():
    return jsonify(
        codelist_codes=codelists.get_db_codelists(),
        codelist_names=list(
            map(lambda codelist: codelist.as_dict(), codelists.get_db_codelist_names())),
        countries=codelists.get_codelists()["Country"],
        organisations=list(map(lambda org: org.as_dict(),
                           qorganisations.get_organisations()))
    )


"""
This should be a command line command

@blueprint.route("/codelists/import_locations/", methods=["POST"])
@login_required
@quser.administrator_required
def import_locations():
    existing_countries = list(map(lambda l: l.country.code,
                    qlocation.get_countries_locations()))
    country_code = request.form.get("country")
    if not country_code in existing_countries:
        qlocation.import_locations(country_code)
        flash("Locations successfully set up for that county!", "success")
    else:
        flash("Locations for that country were not imported, because they have already been imported!", "danger")
    return redirect(url_for("codelists.codelists_management"))
"""


@blueprint.route("/<codelist>/<code_id>.json")
def api_codelist_code(codelist, code_id):
    code = qcodelists.get_code_by_id(codelist, code_id)
    return jsonify(code=code.as_dict())


@blueprint.route("/<codelist>/")
def list_codelist(codelist):
    db_codes = qcodelists.get_codelist(codelist)
    codes = list(map(lambda code: code.as_dict(), db_codes))
    return jsonify(codelists=codes)


@blueprint.route("/organisations/")
def list_organisation_types():
    db_types = qorganisations.get_organisation_types()
    return jsonify(organisation_types=db_types)


@blueprint.route("/organisations/<organisation_type>/")
def list_organisations_by_type(organisation_type):
    db_codes = qorganisations.get_organisations_by_type(organisation_type)
    codes = list(map(lambda org: org.as_dict(), db_codes))
    return jsonify(organisations=codes)


@blueprint.route("/organisations/<organisation_type>/<organisation_id>.json")
def get_organisation(organisation_type, organisation_id):
    code = qorganisations.get_organisation_by_id(organisation_id)
    return jsonify(organisation=code.as_dict())


@blueprint.route("/update/", methods=["POST"])
@jwt_required()
@quser.administrator_required
def api_codelists_update():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.update_attr(request.json)
    else:
        result = qcodelists.update_attr(request.json)
    if result:
        return "OK"
    else:
        return "ERROR"


@blueprint.route("/delete/", methods=["POST"])
@jwt_required()
@quser.administrator_required
def api_codelists_delete():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.delete_org(request.json)
    else:
        result = qcodelists.delete_code(request.json)
    if result:
        return "OK"
    else:
        return "ERROR"


# Need to adjust these permissions
@blueprint.route("/organisations/new/", methods=["POST"])
@jwt_required()
@quser.permissions_required("view")
def api_codelists_new_organisation():
    # FIXME check for admin status
    result = qorganisations.create_organisation(request.json)
    if result:
        return jsonify(organisation=result.as_dict())
    return "ERROR"


@blueprint.route("/new/", methods=["POST"])
@jwt_required()
@quser.administrator_required
def api_codelists_new():
    # FIXME check for admin status
    if request.json["codelist_code"] == "organisation":
        result = qorganisations.create_organisation(request.json)
    else:
        result = qcodelists.create_code(request.json)
    if result:
        return str(result.id)
    else:
        return "ERROR"
