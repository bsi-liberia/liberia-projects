from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user

from maediprojects import app
from maediprojects import db
import models
from views import activities
from query import activity as qactivity

@app.route("/")
def dashboard():
    return render_template("home.html",
                loggedinuser=current_user,
                activities = qactivity.list_activities()
                          )

@app.route("/setup")
def setup():
    db.create_all()
    return "OK"

@app.route("/setup/<country_code>/")
def setup_country(country_code):
    import zipfile