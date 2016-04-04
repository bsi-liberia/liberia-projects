from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
from maediprojects import app, db
import models
from views import activities, api, users, codelists
from query import activity as qactivity
from query import setup as qsetup

@app.route("/setup/")
def setup():
    qsetup.setup()
    return "OK"

@app.route("/setup/<country_code>/")
def setup_country(country_code):
    qsetup.import_locations(country_code)
    return "OK"

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html',
        loggedinuser = current_user), 404
    
@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html',
        loggedinuser = current_user), 500
