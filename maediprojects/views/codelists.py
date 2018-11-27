from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
                            
from maediprojects import app, db, models
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.query import organisations as qorganisations
from maediprojects.query import user as quser
from maediprojects.lib import codelists

import json

@app.route("/codelists/")
@login_required
@quser.administrator_required
def codelists_management():
    return render_template("codelists.html",
                loggedinuser=current_user,
                codelist_codes = codelists.get_db_codelists(),
                codelist_names = codelists.get_db_codelist_names(),
                countries = codelists.get_codelists()["Country"],
                countries_locations = qlocation.get_countries_locations(),
                organisations = qorganisations.get_organisations()
                          )

@app.route("/codelists/import_locations/", methods=["POST"])
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
    return redirect(url_for("codelists_management"))
