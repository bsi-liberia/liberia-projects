import datetime
import functools

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from maediprojects import models
from maediprojects.lib import util


blueprint = Blueprint('management', __name__, url_prefix='/management/', static_folder='../static')


@blueprint.route("/")
@login_required
def management():
    return render_template(
        "management/index.html",
        loggedinuser=current_user
    )


@blueprint.route("/dataquality/")
@login_required
def dataquality():
    return render_template(
        "management/dataquality.html",
        loggedinuser=current_user
    )
