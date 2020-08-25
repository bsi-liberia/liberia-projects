import datetime
import functools

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from maediprojects import models
from maediprojects.query import counterpart_funding as qcounterpart_funding
from maediprojects.lib import util


blueprint = Blueprint('reports', __name__, url_prefix='/', static_folder='../static')


@blueprint.route("/reports/dataquality/")
@login_required
def dataquality_redir():
    return redirect(url_for('management.management'))


@blueprint.route("/reports/milestones/")
@login_required
def milestones():
    activities = models.Activity.query.filter_by(
            domestic_external=u"domestic"
        ).all()
    milestones = models.Milestone.query.filter_by(
            domestic_external=u"domestic"
        ).order_by(
            models.Milestone.milestone_order
        ).all()

    return render_template(
        "reports/milestones.html",
        activities=activities,
        milestones=milestones,
        loggedinuser=current_user
    )


@blueprint.route("/reports/counterpart-funding/")
@login_required
def counterpart_funding():
    activities = models.Activity.query.filter_by(
            domestic_external=u"external"
        ).all()

    activities = qcounterpart_funding.annotate_activities_with_aggregates(
        activities)

    return render_template(
        "reports/counterpart_funding.html",
        fy=util.FY("next").fy_fy(),
        activities = activities,
        loggedinuser = current_user
    )


@blueprint.route("/reports/results/")
@login_required
def results():
    activities = models.Activity.query.filter(
            models.Activity.results.any()
        ).all()

    return render_template(
        "reports/results.html",
        activities = activities,
        loggedinuser = current_user
    )


@blueprint.route("/reports/disbursements/aid/")
@login_required
def aid_disbursements():
    return render_template(
        "reports/aid_disbursements.html",
        loggedinuser=current_user
    )


@blueprint.route("/reports/disbursements/psip/")
@login_required
def psip_disbursements():
    return render_template(
        "reports/psip_disbursements.html",
        loggedinuser=current_user
    )
