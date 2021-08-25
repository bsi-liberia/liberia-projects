from functools import wraps

from werkzeug.security import generate_password_hash
from flask import flash, redirect, url_for, request, make_response, jsonify
from flask_login import current_user

from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.query import organisations as qorganisations
from projectdashboard.query import activity as qactivity
from projectdashboard.query import send_email as qsend_email
from smtplib import SMTPRecipientsRefused

import datetime
import uuid


def administrator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in current_user.roles_list:
            return make_response(jsonify({'msg': 'You must be an administrator to access that page.'}), 403)
        return f(*args, **kwargs)
    return decorated_function


def check_permissions(permission_name, permission_value=None, activity_id=None):
    if "admin" in current_user.roles_list:
        return True
    if permission_name in ("results-data-entry", "results-data-design"):
        if "edit" in current_user.roles_list:
            return True
    if permission_name in ("view") and "view" in current_user.permissions_list:
        return True
    if permission_name in ("view", "edit"):
        if current_user.permissions_dict.get(permission_name, "none") in (permission_value, "both"):
            return True
    if permission_name in ("new"):
        if current_user.permissions_dict.get("edit", "none") != "none":
            return True
        if "desk-officer" in current_user.roles_list:
            return True
    if activity_id:
        check = (check_activity_permissions(permission_name, activity_id))
        if check:
            return True
    return False


def check_activity_permissions(permission_name, activity_id):
    def edit_rights(activity, permissions_search):
        edit_permissions = permissions_search.get("edit", "none")
        if edit_permissions == "both":
            return True
        if edit_permissions == activity.domestic_external:
            return True
        return False
    if "admin" in current_user.roles_list:
        return True
    act = qactivity.get_activity(activity_id)
    if permission_name in ('edit', 'results-data-entry', 'results-data-design'):
        if edit_rights(act, current_user.permissions_dict):
            return True
        # For now, we allow all users with results design / data entry roles
        # to add results data for all projects
        if permission_name in current_user.roles_list:
            return True
    if act and current_user.permissions_dict.get("organisations"):
        if (act.reporting_org_id in current_user.permissions_dict["organisations"]):
            # If the user is attached to an organisation, then they should always
            # at least have view rights.
            if permission_name == "view":
                return True
            if permission_name == "edit":
                if edit_rights(act, current_user.permissions_dict["organisations"][act.reporting_org_id]):
                    return True
            if permission_name in current_user.permissions_list["organisations"][act.reporting_org_id]:
                return True
            elif permission_name in ("results-data-entry", "results-data-design"):
                if "edit" in current_user.permissions_list["organisations"][act.reporting_org_id]:
                    return True
    return False


def check_new_activity_permission():
    for org in current_user.permissions_dict["organisations"].values():
        if org["permission_value"] == "edit":
            return True
    return False


def permissions_required(permission_name, permission_value=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "admin" in current_user.roles_list:
                check = True
            elif kwargs.get('activity_id'):
                activity_id = kwargs.get('activity_id')
                check = (check_activity_permissions(permission_name, activity_id)
                         or check_permissions(permission_name, permission_value))
            elif permission_name == "new":
                check = (check_new_activity_permission() or check_permissions(
                    permission_name, permission_value))
            elif permission_name == "edit":
                check = (check_new_activity_permission() or check_permissions(
                    permission_name, permission_value))
            else:
                check = (check_permissions(permission_name, permission_value))
            if check is False:
                return make_response(jsonify({'msg': 'You do not have sufficient permissions to access that page.'}), 403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


def user(user_id=None):
    if user_id:
        user = models.User.query.filter_by(id=user_id
                                           ).first()
        return user
    else:
        users = models.User.query.all()
        return users


def role(role_slug=None):
    if role_slug:
        role = models.Role.query.filter_by(
            slug=role_slug).first()
        return role
    else:
        roles = models.Role.query.all()
        return roles


def role_by_slug(role_slug):
    role = models.Role.query.filter_by(slug=role_slug
                                       ).first()
    return role


def users_with_role(role_slug):
    users = db.session.query(models.User
                             ).join(models.UserRole
                                    ).join(models.Role
                                           ).filter(models.Role.slug == role_slug
                                                    ).all()
    return users


def add_user_role(username, role_slug):
    user = user_by_username(username)
    role = role_by_slug(role_slug)
    if (user and role):
        ur = models.UserRole()
        ur.user_id = user.id
        ur.role_id = role.id
        db.session.add(ur)
        db.session.commit()
        return True
    return False


def list_user_role_by_username(username):
    user = user_by_username(username)
    if not user:
        return False
    return user.roles_list


def delete_user_role(username, role_slug):
    user = user_by_username(username)
    role = role_by_slug(role_slug)
    if (user and role):
        ur = models.UserRole.query.filter_by(
            user_id=user.id,
            role_id=role.id).first()
        if not ur:
            return False
        db.session.delete(ur)
        db.session.commit()
        return True
    return False


def user_id_username():
    users = models.User.query.all()
    return list(map(lambda u: {
        "id": u.id,
        "username": u.username,
        "name": u.name,
        "organisation": u.organisation,
        "user_roles": list(map(lambda ur: ur.role.as_dict(), u.userroles)),
        "editable": True}, users))


def activitylog(offset=0, user_id=None):
    activitylogs = models.ActivityLog.query
    if user_id:
        activitylogs = activitylogs.filter_by(
            user_id=user_id)
    activitylogs = activitylogs.order_by(
        models.ActivityLog.id.desc()
    ).offset(offset
             ).limit(10
                     ).all()
    return activitylogs


def activitylog_detail(activitylog_id):
    activitylog = models.ActivityLog.query.filter_by(
        id=activitylog_id).first()
    return activitylog


def user_by_username(username=None):
    if username:
        user = models.User.query.filter_by(username=username
                                           ).first()
        return user
    return None


def user_by_email_address(email_address=None):
    if email_address:
        user = models.User.query.filter_by(email_address=email_address
                                           ).first()
        return user
    return None


def setPermission(user, permission_name, permission_value):
    checkPermission = models.UserPermission.query.filter_by(
        user_id=user.id,
        permission_name=permission_name).first()
    if not checkPermission:
        checkPermission = models.UserPermission()
        checkPermission.user_id = user.id
        checkPermission.permission_name = permission_name
    checkPermission.permission_value = permission_value
    db.session.add(checkPermission)
    db.session.commit()
    return checkPermission


def updateUser(data):
    checkU = models.User.query.filter_by(id=data["id"]
                                         ).first()
    assert checkU
    checkU.username = data["username"]
    checkU.name = data["name"]
    checkU.email_address = data["email_address"]
    checkU.organisation = data["organisation"]
    checkU.recipient_country_code = data["recipient_country_code"]

    if "change_password" in data:
        # Update password
        checkU.pw_hash = generate_password_hash(data["password"])

    if "admin" in current_user.roles_list:
        # Only an admin user can give administrative privileges
        setPermission(checkU, u"view", data.get("view", "none"))
        setPermission(checkU, u"edit", data.get("edit", "none"))

    db.session.add(checkU)
    db.session.commit()

    # This should be done more nicely on the model...
    if "admin" in current_user.roles_list:
        current_user_roles = list(map(lambda ur: ur.role_id, checkU.userroles))
        new_user_roles = filter(lambda r: r != '', data.get("user_roles", []))
        roles_to_add = filter(
            lambda r: r not in current_user_roles, new_user_roles)
        roles_to_delete = filter(
            lambda r: r not in new_user_roles, current_user_roles)
        for role_id in roles_to_delete:
            ur = models.UserRole.query.filter_by(
                user_id=checkU.id, role_id=int(role_id)).first()
            if (current_user.id == ur.id) and (ur.role.slug == "admin"):
                flash("As an administrator, you cannot remove administrative privileges from yourself. If you would like to remove administrative privileges from this account then you must log in as another user.", "danger")
                continue
            db.session.delete(ur)
        for role_id in roles_to_add:
            ur = models.UserRole()
            ur.user_id = checkU.id
            ur.role_id = role_id
            db.session.add(ur)
    db.session.commit()
    return checkU


def addUser(data):
    checkU = models.User.query.filter_by(username=data["username"]
                                         ).first()
    if not checkU:
        newU = models.User()
        newU.setup(
            username=data["username"],
            password=data.get('password'),
            name=data.get('name'),
            email_address=data.get('email_address'),
            organisation=data.get('organisation'),
            recipient_country_code=data.get('recipient_country_code')
        )
        db.session.add(newU)
        db.session.commit()
        setPermission(newU, u"view", data.get("view"))
        setPermission(newU, u"edit", data.get("edit"))

        if data.get("administrator") == True:
            add_user_role(data["username"], "admin")
        new_user_roles = filter(lambda r: r != '', data.get("user_roles", []))
        for role_id in new_user_roles:
            ur = models.UserRole()
            ur.user_id = newU.id
            ur.role_id = role_id
            db.session.add(ur)
        db.session.commit()

        return newU
    return checkU


def addUserPermission(data):
    checkP = models.UserPermission.query.filter_by(
        user_id=data["user_id"],
        permission_name=data.get("permission_name"),
        organisation_slug=data["organisation_slug"],
    ).first()
    if not checkP:
        newP = models.UserPermission()
        newP.setup(
            user_id=data["user_id"],
            permission_name=data.get("permission_name"),
            organisation_slug=data["organisation_slug"],
        )
        db.session.add(newP)
        db.session.commit()
        return newP
    return None


def deleteUserPermission(permission_id):
    checkP = models.UserPermission.query.filter_by(id=permission_id).first()
    if checkP:
        db.session.delete(checkP)
        db.session.commit()
        return True
    return None


def deleteUser(username):
    checkU = models.User.query.filter_by(username=username).first()
    if checkU:
        db.session.delete(checkU)
        db.session.commit()
        return True
    return None


def userPermissions(user_id):
    checkP = models.UserPermission.query.filter_by(user_id=user_id
                                                   ).all()
    return checkP


def addOrganisationPermission(data):
    checkOP = models.UserOrganisation()
    checkOP.user_id = data['user_id']
    checkOP.permission_name = data["permission_name"]
    checkOP.permission_value = data["permission_value"]
    checkOP.organisation_id = qorganisations.get_organisation_by_code("").id
    db.session.add(checkOP)
    db.session.commit()
    return checkOP


def deleteOrganisationPermission(data):
    checkOP = models.UserOrganisation.query.filter_by(id=data['id']).first()
    db.session.delete(checkOP)
    db.session.commit()
    return True


def updateOrganisationPermission(data):
    checkOP = models.UserOrganisation.query.filter_by(id=data['id']).first()
    if not checkOP:
        return False
    setattr(checkOP, data['attr'], data['value'])
    db.session.add(checkOP)
    db.session.commit()
    return checkOP


def check_password_reset(email_address, reset_password_key):
    user = models.User.query.filter(models.User.email_address == email_address,
                                    models.User.reset_password_key == reset_password_key,
                                    models.User.reset_password_expiry > datetime.datetime.now()
                                    ).first()
    if user:
        return True
    return False


def process_reset_password(email_address, reset_password_key, password):
    if not check_password_reset(email_address, reset_password_key):
        return False
    user = user_by_email_address(email_address)
    user.pw_hash = generate_password_hash(password)
    user.reset_password_key = None
    user.reset_password_expiry = None
    db.session.add(user)
    db.session.commit()
    return True


def send_unknown_user_password_reset_email(email_address):
    message_body = """
LIBERIA PROJECT DASHBOARD

Reset Password
==============

Someone, possibly you, requested to reset your password on the Liberia Project Dashboard.

However, there was no account found associated with this email address. Please contact MFDP if you think this is in error, or if you would like an account to be created for you.
    """
    qsend_email.send_async_email(
        message_recipient=email_address,
        message_subject="Liberia Project Dashboard - Password Reset",
        message_body=message_body)


def send_user_password_reset_email(email_address, user):
    message_body = """
LIBERIA PROJECT DASHBOARD

Reset Password
==============

Someone, possibly you, requested to reset your password on the Liberia Project Dashboard.

Your username is: {}

If you didn't request your password to be reset, please ignore this message.

If you would like to reset your password, please click the following link:
{}

If you can't click the link, go to the following page:
{}

And copy/paste the following password reset key into the box:
{}
    """.format(
        user.username,
        "{}users/reset-password/key/?email_address={}&reset_password_key={}".format(
            request.url_root,
            email_address,
            user.reset_password_key
        ),
        "{}users/reset-password/key/?email_address={}".format(
            request.url_root,
            email_address
        ),
        user.reset_password_key
    )
    qsend_email.send_async_email(
        message_recipient=email_address,
        message_subject="Liberia Project Dashboard - Password Reset",
        message_body=message_body)


def make_password_reset_key(email_address):
    try:
        user = user_by_email_address(email_address)
        if not user:
            send_unknown_user_password_reset_email(email_address)
        else:
            user.reset_password_key = uuid.uuid4().hex
            user.reset_password_expiry = datetime.datetime.now() + datetime.timedelta(days=1)
            db.session.add(user)
            db.session.commit()
            send_user_password_reset_email(email_address, user)
        return True
    except SMTPRecipientsRefused:
        flash("Could not send an email to that address. Please confirm you provided a valid email address and try again. The email address you provided was: {}".format(
            email_address), "danger")
        return False
