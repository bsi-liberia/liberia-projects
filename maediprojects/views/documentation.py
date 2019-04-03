import os
import datetime
import functools

from flask import Blueprint, Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, jsonify
from flask_login import login_required, current_user

from maediprojects import models
from maediprojects.extensions import db
from maediprojects.views import activities, api, users, codelists
from maediprojects.query import activity as qactivity
from maediprojects.lib import util

import re
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.tables import TableExtension

blueprint = Blueprint('documentation', __name__, url_prefix='/', static_folder='../static')


@blueprint.route("/help/")
@login_required
def help():
    current_dir = os.path.join(os.path.dirname(__file__))
    help_content = open(os.path.join(current_dir, "../templates/help.md"), "r").read()

    output_text = re.sub("<table>", '<table class="table">', markdown.markdown(help_content,
        extensions=[TocExtension(baselevel=1,
            title="Overview", toc_depth="2-3"), TableExtension()]))
    return render_template("help.html",
                markdown_text = Markup(output_text),
                loggedinuser=current_user
        )
