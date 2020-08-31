from flask import Blueprint, render_template, flash, request, redirect, url_for, abort, make_response
from flask_login import current_user, login_required, login_user, logout_user
from flask_jwt_extended import (
    jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, get_raw_jwt
)
from flask_babel import gettext

from maediprojects import models
from maediprojects.query import user as quser
from maediprojects.query import organisations as qorganisations
from maediprojects.lib import codelists
from maediprojects.views.api import jsonify
from maediprojects.extensions import login_manager


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


@blueprint.route("/profile/", methods=["GET", "POST"])
@login_required
def profile():
    if "admin" in current_user.roles_list:
        return redirect(url_for("users.users_edit", user_id=current_user.id))

    if request.method == "POST":
        data = {
            k: v
            for k, v in request.form.items()
            if k in ["name", "organisation", "recipient_country_code",
                     "change_password", "password"]
        }
        data["id"] = current_user.id
        data["username"] = current_user.username
        data["email_address"] = current_user.email_address

        if quser.updateUser(data):
            flash(gettext(u"Profile successfully updated!"), "success")
        else:
            flash(gettext(u"Sorry, couldn't update!"), "danger")
        return redirect(url_for("users.profile"))

    return render_template("users/profile.html",
                           codelists=codelists.get_codelists(),
                           user=current_user,
                           loggedinuser=current_user)


@blueprint.route("/api/user/")
@jwt_required
def user():
    return jsonify(user=current_user.as_simple_dict())


@blueprint.route("/users/")
@login_required
@quser.administrator_required
def users():
    if "admin" not in current_user.roles_list:
        flash(gettext(u"You must be an administrator to access that area."), "danger")
    users = quser.user()
    return render_template("users/users.html",
                           users=users,
                           loggedinuser=current_user)


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


@blueprint.route("/users/log/")
@login_required
@quser.administrator_required
def users_log():
    userslog = quser.activitylog()
    return render_template("users/userslog.html",
                           userslog=userslog,
                           loggedinuser=current_user)


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


@blueprint.route("/reset-password/password/", methods=["GET", "POST"])
def reset_password_new_password():
    if request.method == "GET":
        return render_template("users/reset_password_password.html",
            email_address=request.args.get("email_address"),
            reset_password_key=request.args.get("reset_password_key"),
            loggedinuser=current_user
            )
    else:
        if not (request.form.get("password") == request.form.get("password_2")):
            flash("Please make sure you enter the same password twice.", "danger")
        elif request.form.get("password") == "":
            flash("Please enter a password.", "danger")
        else:
            if quser.process_reset_password(
                email_address=request.form.get("email_address"),
                reset_password_key=request.form.get("reset_password_key"),
                password=request.form.get("password")
                ):
                flash("Password successfully changed! Please login with your new password.", "success")
                return redirect(url_for('users.login'))
            else:
                flash("Sorry, something went wrong, and your password could not be changed.", "danger")
    return render_template("users/reset_password_password.html",
        email_address=request.args.get("email_address"),
        reset_password_key=request.args.get("reset_password_key"),
        loggedinuser=current_user
        )


@blueprint.route("/reset-password/key/", methods=["GET", "POST"])
def reset_password_with_key():
    if ((request.method == "GET") and
        (request.args.get("email_address", "") != "") and
        (request.args.get("reset_password_key", "") != "")):
        if quser.check_password_reset(request.args["email_address"], request.args["reset_password_key"]):
            return redirect(url_for('users.reset_password_new_password',
                email_address=request.args.get("email_address"),
                reset_password_key=request.args.get("reset_password_key")
                ))
        flash("Sorry, could not reset that passsword key. Please try resetting your password again, and make sure you use the reset key within 24 hours.", "danger")
        return redirect(url_for('users.reset_password'))

    elif request.method == "POST":
        if (request.form.get("email_address", "") != "") and (request.form.get("reset_password_key", "") != ""):
            if quser.check_password_reset(request.form["email_address"], request.form["reset_password_key"]):
                return redirect(url_for('users.reset_password_new_password',
                    email_address=request.form.get("email_address"),
                    reset_password_key=request.form.get("reset_password_key")
                    ))
            flash("Sorry, could not reset that passsword key. Please try resetting your password again, and make sure you use the reset key within 24 hours.", "danger")
            return redirect(url_for('users.reset_password'))
        else:
            flash(gettext(u"Please enter an email address and key."), "danger")
    email_address = request.args.get('email_address', "")
    return render_template("users/reset_password_with_key.html",
            email_address=email_address,
            loggedinuser=current_user)


@blueprint.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        if request.form.get("email_address", "") != "":
            if quser.make_password_reset_key(request.form["email_address"]):
                flash(gettext(u"Sent an email to {} - please check your email for further instructions on how to reset your password.".format(request.form['email_address'])), "success")
                return redirect(url_for('users.reset_password_with_key',
                    email_address=request.form["email_address"]))
        else:
            flash(gettext(u"Please enter an email address."), "danger")
    return render_template("users/reset_password.html",
             loggedinuser=current_user)


@blueprint.route('/api/logout/')
@login_required
def logout():
    logout_user()
    flash(gettext(u'Logged out'), 'success')
    redir_url = url_for("users.login")
    return redirect(redir_url)
