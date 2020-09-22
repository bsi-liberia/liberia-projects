from flask import Blueprint, flash, request, redirect, url_for, abort, make_response
from flask_login import current_user, login_required, login_user, logout_user
from flask_jwt_extended import (
    jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, get_raw_jwt, jwt_optional
)
from flask_babel import gettext

from maediprojects import models
from maediprojects.query import user as quser
from maediprojects.query import organisations as qorganisations
from maediprojects.lib import codelists
from maediprojects.views.api import jsonify
from maediprojects.extensions import login_manager, UnauthenticatedUser


blueprint = Blueprint('users', __name__, url_prefix='/', static_folder='../static')


@login_manager.request_loader
def load_user_from_request(request):
    current_user = get_jwt_identity()
    if current_user is None: return None
    user = models.User.query.filter_by(username=current_user).first()
    if user:
        return user
    return None


@login_manager.user_loader
def load_user(user_id):
    return models.User.query.filter_by(id=user_id).first_or_404()


@blueprint.route("/api/unauthenticated_user/")
def unauthenticated_user():
    return jsonify(user=UnauthenticatedUser().as_simple_dict())


@blueprint.route("/api/user/")
@jwt_optional
def user():
    return jsonify(user=current_user.as_simple_dict())


@blueprint.route("/api/users/delete/", methods=["POST"])
@jwt_required
@quser.administrator_required
def users_delete():
    if "admin" not in current_user.roles_list:
        return make_response(
            jsonify({'msg': "You must be an administrator to delete users."}),
            403)
    if current_user.username == request.get_json().get("username"):
        return make_response(
            jsonify({'msg': "You cannot delete your own user."}),
            400)
    if quser.deleteUser(request.get_json().get('username')):
        return make_response(
            jsonify({'msg': "Successfully deleted user."}),
            200)
    return make_response(
        jsonify({'msg': "Sorry, there was an error and that user could not be deleted."}),
        500)


@blueprint.route("/api/users/new/", methods=["GET", "POST"])
@jwt_required
@quser.administrator_required
def users_new():
    if request.method == "GET":
        user = {
            "view": current_user.permissions_dict["view"],
            "edit": 'none',
            "recipient_country_code": "LR"
        }
        roles = list(map(lambda r: r.as_dict(), models.Role.query.all()))
        return make_response(jsonify(
            user=user,
            roles=roles), 200)
    elif request.method == "POST":
        user = quser.addUser(request.json)
        if user:
            return make_response(jsonify({
                'msg': 'Successfully created user!',
                'user': user.as_dict()
            }), 200)
        else:
            return make_response(jsonify({'msg': "Sorry, couldn't create that user!"}), 500)


@blueprint.route("/api/users/<user_id>/", methods=["GET", "POST"])
@jwt_required
@quser.administrator_required
def users_edit(user_id):
    user = quser.user(user_id)
    if user == None: return abort(404)
    roles = list(map(lambda r: r.as_dict(), models.Role.query.all()))

    def annotate_user(user):
        _user = user.as_dict()
        _user['view'] = user.permissions_dict["view"]
        _user['edit'] = user.permissions_dict["edit"]
        return _user

    if request.method == "GET":
        return jsonify(
            user=annotate_user(user),
            roles=roles)
    elif request.method == "POST":
        data = request.json
        data["id"] = user_id
        if quser.updateUser(data):
            return make_response(jsonify({'msg': "Successfully updated user!"}), 200)
        else:
            return make_response(jsonify({'msg': "Sorry, couldn't update that user!"}), 500)


@blueprint.route("/api/users/<user_id>/permissions/", methods=["GET", "POST"])
@jwt_required
@quser.administrator_required
def user_permissions_edit(user_id):
    if request.method == "GET":
        user = quser.user(user_id)
        if user == None: return abort(404)
        user_organisations = list(map(lambda uo: uo.as_dict(), user.organisations))
        user_roles = list(map(lambda uo: uo.as_dict(), user.userroles))
        roles = list(map(lambda r: r.as_dict(), models.Role.query.all()))
        organisations = list(map(lambda o: o.as_dict(), qorganisations.get_organisations()))
        permission_values = [
            {"name": "View projects", "value": "view"},
            {"name": "Edit projects", "value": "edit"},
            {"name": "Results data entry", "value": "results-data-entry"},
            {"name": "Results data design", "value": "results-data-design"}
        ]
        return jsonify(permissions=user_organisations,
            organisations=organisations,
            permission_values=permission_values,
            user_roles=user_roles,
            roles=roles)
    elif request.method == "POST":
        data = request.get_json()
        data["user_id"] = user_id
        if data["action"] == "add":
            op = quser.addOrganisationPermission(data)
            if not op: return "False"
            return jsonify(op.as_dict())
        elif data["action"] == "delete":
            op = quser.deleteOrganisationPermission(data)
            if not op:
                return "error"
            return "ok"
        elif data["action"] == "edit":
            op = quser.updateOrganisationPermission(data)
            if not op:
                return "error"
            return "ok"
        return "error, unknown action"


@blueprint.route("/api/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.json:
        if not request.is_json:
            return make_response(jsonify({"msg": "Missing JSON in request"}), 400)
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        if not username:
            return make_response(jsonify({"msg": "Missing username parameter"}), 400)
        if not password:
            return make_response(jsonify({"msg": "Missing password parameter"}), 400)

        user = models.User.query.filter_by(username=username).first()
        if not (user and user.check_password(password) and user.is_active()):
            return make_response(jsonify({"msg": "Bad username or password"}), 401)

        # Identity can be any data that is json serializable
        ret = {
            'access_token': create_access_token(identity=username),
            'refresh_token': create_refresh_token(identity=username)
        }
        return make_response(jsonify(ret), 200)
    return make_response(jsonify({"msg": "Please login to continue."}), 200)


@blueprint.route("/api/reset-password/password/", methods=["POST"])
def reset_password_new_password():
    if not (request.json.get("password") == request.json.get("password_2")):
        return make_response(jsonify({'msg': 'Please make sure you enter the same password twice.'}), 400)
    elif request.json.get("password") == "":
        return make_response(jsonify({'msg': 'Please enter a password.'}), 400)
    else:
        if quser.process_reset_password(
            email_address=request.json.get("email_address"),
            reset_password_key=request.json.get("reset_password_key"),
            password=request.json.get("password")
            ):
            return make_response(jsonify({'msg': 'Password successfully changed! Please login with your new password.'}), 200)
        else:
            return make_response(jsonify({'msg': 'Sorry, something went wrong, and your password could not be changed.'}), 400)


@blueprint.route("/api/reset-password/key/", methods=["POST"])
def reset_password_with_key():
    if (request.json.get("email_address", "") != "") and (request.json.get("reset_password_key", "") != ""):
        if quser.check_password_reset(request.json["email_address"], request.json["reset_password_key"]):
            return make_response(jsonify({'msg': 'Key authenticated - please provide a new password.'}), 200)
        return make_response(jsonify({'msg': 'Sorry, could not reset that passsword key. Please try resetting your password again, and make sure you use the reset key within 24 hours.'}), 400)
    else:
        return make_response(jsonify({'msg': "Please enter an email address and key."}), 400)


@blueprint.route("/api/reset-password/", methods=["POST"])
def reset_password():
    email_address = request.json.get('email_address', '')
    if email_address != "":
        if quser.make_password_reset_key(email_address):
            return make_response(jsonify({'msg': 'Sent an email to {} - please check your email for further instructions on how to reset your password.'.format(email_address)}), 200)
    else:
        return make_response(jsonify({'msg': 'Please enter an email address.'}), 400)


@blueprint.route('/api/logout/')
@jwt_optional
def logout():
    return make_response(jsonify({'msg': 'Logged out successfully'}), 200)
