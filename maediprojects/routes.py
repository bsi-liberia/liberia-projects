from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask_login import login_required, current_user
from maediprojects import app, db
import models
from views import activities, api, users, codelists, documentation
from query import activity as qactivity
import os
import mistune

@app.before_request
def setup_default_permissions():
    if current_user.is_authenticated:
        session["permissions"] = current_user.permissions_dict
    else:
        session["permissions"] = {}
        if request.headers['Host'] == "psip.liberiaprojects.org":
            session["permissions"]["domestic_external"] = "domestic"
        elif request.headers['Host'] == "liberiaprojects.org":
            session["permissions"]["domestic_external"] = "external"
        # Only used for bug testing locally
        elif request.headers['Host'] == "127.0.0.1:5000":
            session["permissions"]["domestic_external"] = "domestic"
        else:
            session["permissions"]["domestic_external"] = "both"


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html',
        loggedinuser = current_user), 404
    
@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html',
        loggedinuser = current_user), 500
