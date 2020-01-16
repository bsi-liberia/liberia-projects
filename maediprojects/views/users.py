from flask import Blueprint, render_template, flash, request, redirect, url_for, abort
from flask_login import current_user, login_required, login_user, logout_user
from flask_babel import gettext

from maediprojects import models
from maediprojects.query import user as quser
from maediprojects.query import organisations as qorganisations
from maediprojects.lib import codelists
from maediprojects.views.api import jsonify
from maediprojects.extensions import login_manager


blueprint = Blueprint('users', __name__, url_prefix='/', static_folder='../static')


@login_manager.user_loader
def load_user(id):
    return models.User.query.get(id)


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


@blueprint.route("/users/delete/", methods=["POST"])
@login_required
@quser.administrator_required
def users_delete():
    if "admin" not in current_user.roles_list:
        flash(gettext(u"You must be an administrator to create new users."), "danger")
        return redirect(url_for("activities.dashboard"))
    if current_user.username == request.get_json().get("username"):
        flash(gettext(u"You cannot delete your own user."), "danger")
        return redirect(url_for("activities.dashboard"))
    if quser.deleteUser(request.get_json().get('username')):
        flash(gettext(u"Successfully deleted user."), "success")
    else:
        flash(gettext(u"Sorry, there was an error and that user could not be deleted."), "danger")
    return redirect(url_for("users.users"))


@blueprint.route("/users/new/", methods=["GET", "POST"])
@login_required
@quser.administrator_required
def users_new():
    if request.method == "GET":
        user = {
            "permissions_dict": {
                "view": current_user.permissions_dict["view"]
            },
            "recipient_country_code": "LR"
        }
        return render_template("users/user.html",
                               user=user,
                               loggedinuser=current_user,
                               codelists=codelists.get_codelists())
    elif request.method == "POST":
        user = quser.addUser(request.form)
        if user:
            flash(gettext(u"Successfully created user!"), "success")
            return redirect(url_for("users.users_edit", user_id=user.id))
        else:
            flash(gettext(u"Sorry, couldn't create that user!"), "danger")
        return redirect(url_for("users.users"))


@blueprint.route("/users/<user_id>/", methods=["GET", "POST"])
@login_required
@quser.administrator_required
def users_edit(user_id):
    user = quser.user(user_id)
    if request.method == "GET":
        if not user:
            return abort(404)
        return render_template("users/user.html",
                 user=user,
                 loggedinuser=current_user,
                 organisations=qorganisations.get_organisations(),
                 codelists=codelists.get_codelists())
    elif request.method == "POST":
        data = request.form.to_dict()
        data["id"] = user_id
        if quser.updateUser(data):
            flash(gettext(u"Successfully updated user!"), "success")
        else:
            flash(gettext(u"Sorry, couldn't update that user!"), "danger")
        return redirect(url_for("users.users_edit", user_id=user_id))


@blueprint.route("/users/<user_id>/permissions/", methods=["GET", "POST"])
@login_required
@quser.administrator_required
def user_permissions_edit(user_id):
    if request.method == "GET":
        user = quser.user(user_id)
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


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        user = quser.user_by_username(request.form["username"])
        remember = True if request.form.get('remember') else False
        if (user and user.check_password(request.form["password"])):
            if login_user(user, remember=remember):
                flash(gettext(u"Logged in!"), "success")
                if request.args.get("next"):
                    redir_url = request.script_root + request.args.get("next")
                else:
                    redir_url = url_for("activities.dashboard")
                return redirect(redir_url)
            else:
                flash(gettext(u"Sorry, but you could not log in."), "danger")
        else:
            flash(gettext(u"Invalid username or password."), "danger")
    return render_template("users/login.html",
             loggedinuser=current_user)


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


@blueprint.route('/logout/')
@login_required
def logout():
    logout_user()
    flash(gettext(u'Logged out'), 'success')
    redir_url = url_for("users.login")
    return redirect(redir_url)
