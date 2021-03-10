from maediprojects.views.api import jsonify
from maediprojects.query import user as quser
from maediprojects.query import activity as qactivity
from maediprojects.query import exchangerates as qexchangerates
from maediprojects.query import finances as qfinances

from flask import Blueprint, request, abort
from flask_login import current_user

from flask_jwt_extended import (
    jwt_required
)
from maediprojects.lib import util
from maediprojects import models


blueprint = Blueprint('activity_finances', __name__, url_prefix='/api/activity_finances')


@blueprint.route("/<activity_id>/", methods=["POST", "GET"])
@jwt_required()
@quser.permissions_required("edit")
def api_activity_finances(activity_id):
    """GET returns a list of all financial data for a given activity_id.
    POST also accepts financial data to be added or deleted."""
    activity = qactivity.get_activity(activity_id)
    if activity == None: return abort(404)
    if request.method == "POST":
        request_data = request.get_json()
        if request_data["action"] == "add":
            print(request_data)
            data = {
                "transaction_type": request_data["transaction_type"],
                "transaction_date": request_data["transaction_date"],
                "transaction_value_original": request_data["transaction_value_original"],
                "aid_type": request_data.get("aid_type", activity.aid_type),
                "finance_type": request_data.get("finance_type", activity.finance_type),
                "provider_org_id": request_data.get("provider_org_id", activity.funding_organisations[0].id),
                "receiver_org_id": request_data.get("receiver_org_id", activity.implementing_organisations[0].id),
                "fund_source_id": request_data.get("fund_source_id", None),
                "currency": request_data.get("currency", u"USD"),
                "classifications": {
                    "mtef-sector": request_data.get("mtef_sector",
                        activity.classification_data['mtef-sector']['entries'][0].codelist_code_id)
                }
            }
            result = qfinances.add_finances(activity_id, data).as_simple_dict()
        elif request_data["action"] == "delete":
            result = qfinances.delete_finances(activity_id, request.get_json()["transaction_id"])
        if result:
            return jsonify(result)
        else: return abort(500)
    elif request.method == "GET":
        finances = {
            'commitments': list(map(lambda t: t.as_dict(), activity.commitments)),
            'allotments': list(map(lambda t: t.as_dict(), activity.allotments)),
            'disbursements': list(map(lambda t: t.as_dict(), activity.disbursements))
        }
        fund_sources = list(map(lambda fs: {
            "id": fs.id, "name": fs.name
            }, models.FundSource.query.all()))
        return jsonify(
            finances = finances,
            fund_sources = fund_sources
        )


@blueprint.route("/<activity_id>/update_finances/", methods=['POST'])
@jwt_required()
@quser.permissions_required("edit")
def finances_edit_attr(activity_id):
    request_data = request.get_json()
    data = {
        'activity_id': activity_id,
        'attr': request_data['attr'],
        'value': request_data['value'],
        'finances_id': request_data['finances_id'],
    }

    #Run currency conversion if:
    # we now set to automatic
    # we change the currency and have set to automatic
    if (data.get("attr") == "transaction_date") and (data.get("value") == ""):
        return abort(500)
    if (data.get("attr") == "currency_automatic") and (data.get("value") == True):
        # Handle update, and then return required data
        update_status = qexchangerates.automatic_currency_conversion(
            finances_id = data["finances_id"],
            force_update = True)
        return jsonify(update_status.as_dict())
    elif (data.get("attr") in ("currency", "transaction_date")):
        update_curency = qfinances.update_attr(data)
        update_status = qexchangerates.automatic_currency_conversion(
            finances_id = data["finances_id"],
            force_update = False)
        return jsonify(update_status.as_simple_dict())
    elif data["attr"] == "mtef_sector":
        data["attr"] = 'mtef-sector' #FIXME make consistent
        update_status = qfinances.update_finances_classification(data)
    else:
        update_status = qfinances.update_attr(data)
    if update_status:
        return jsonify(update_status.as_simple_dict())
    return abort(500)
