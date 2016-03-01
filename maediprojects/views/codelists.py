from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
                            
from maediprojects import app, db, models
from maediprojects.query import activity as qactivity
from maediprojects.query import location as qlocation
from maediprojects.lib import codelists

import json

@app.route("/codelists/")
@login_required
def codelists_management():
    return render_template("codelists.html",
                loggedinuser=current_user,
                codelist_codes = codelists.get_db_codelists(),
                codelist_names = codelists.get_db_codelist_names()
                          )
