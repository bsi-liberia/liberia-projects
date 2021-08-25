from flask import Blueprint, flash, request, \
    redirect, url_for, jsonify, abort, current_app
from flask_login import login_required, current_user
from projectdashboard.query import user as quser
from projectdashboard.query import admin as qadmin
from projectdashboard.query import activity as qactivity
from projectdashboard import models
from flask_jwt_extended import jwt_required
import datetime


blueprint = Blueprint('admin', __name__, url_prefix='/api/admin')


@blueprint.route("/fiscal-year-choices/", methods=["POST", "GET"])
@jwt_required()
@quser.administrator_required
def api_fiscal_year_choices():
    if request.method == 'GET':
        db_fiscal_year_choices = models.FiscalYearChoice.query.all()
        fiscal_year_choices = list(
            map(lambda fiscal_year: fiscal_year.as_dict(), db_fiscal_year_choices))
        earliest_date = current_app.config['EARLIEST_DATE']
        latest_date = current_app.config['LATEST_DATE']
        return jsonify({
            'fiscalYearChoices': fiscal_year_choices,
            'earliestDate': earliest_date.isoformat(),
            'latestDate': latest_date.isoformat()
        })
    elif request.method == 'POST':
        fiscal_years = request.get_json()
        success = qadmin.process_fiscal_years(fiscal_years)
        if not success:
            return abort(400)
        return jsonify({'updated': True})
