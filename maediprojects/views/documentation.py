from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask.ext.login import login_required, current_user
from maediprojects import app, db, models
from maediprojects.views import activities, api, users, codelists
from maediprojects.query import activity as qactivity
import os
import mistune

@app.route("/help/")
@login_required
def help():
    current_dir = os.path.join(os.path.dirname(__file__))
    help_content = open(os.path.join(current_dir, "../templates/help.md"), "r").read()
    return render_template("help.html",
                markdown_text = Markup(mistune.markdown(help_content)),
                loggedinuser=current_user
        )

@app.route("/milestones/")
@login_required
def milestones():
    activities = models.Activity.query.filter_by(
            domestic_external="domestic"
        ).all()
    milestones = models.Milestone.query.filter_by(
        domestic_external="domestic"
        ).order_by(models.Milestone.milestone_order
        ).all()

    """

    milestones_dict = dict(map(lambda m: (m.id, m.as_dict()), milestones))

    activities_milestones_dict = list(map(lambda a: a.id, a.title))
    """

    return render_template("milestones.html",
                activities = activities,
                milestones = milestones,
                loggedinuser=current_user
        )