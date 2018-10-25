from maediprojects import db, models
from werkzeug.security import generate_password_hash, check_password_hash
import datetime, time
from flask import flash, redirect, url_for, request
from flask.ext.login import current_user
from functools import wraps

def administrator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.administrator is False:
            flash("You must be an administrator to access that page.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def check_permissions(permission_name):
    if current_user.permissions_dict.get(permission_name, "none") == "none":
        return False
    return True

def permissions_required(permission_name):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permissions(permission_name):
                flash("You do not have sufficient permissions to access that page.", "danger")
                if request.referrer != None:
                    return redirect(request.referrer)
                return redirect(url_for("dashboard"))
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

def user_by_username(username=None):
    if username:
        user = models.User.query.filter_by(username=username
                    ).first()
        return user
    return None

def setPermission(user, permission_name, permission_value):
    checkPermission = models.UserPermission.query.filter_by(
        user_id = user.id,
        permission_name = permission_name).first()
    if not checkPermission:
        checkPermission = models.UserPermission()
        checkPermission.user_id=user.id
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
    
    # Only an admin user can give administrative privileges
    if not current_user.administrator and data.get('administrator'):
        data.pop('administrator')
        
    checkU.administrator = bool(data.get('administrator'))
    if "change_password" in data:
        # Update password
        checkU.pw_hash = generate_password_hash(data["password"])
    setPermission(checkU, "domestic_external", data.get("domestic_external", "none"))
    setPermission(checkU, "domestic_external_edit", data.get("domestic_external_edit", "none"))
    db.session.add(checkU)
    db.session.commit()
    return checkU

def addUser(data):
    checkU = models.User.query.filter_by(username=data["username"]
                ).first()
    if not checkU:
        newU = models.User()
        newU.setup(
            username = data["username"],
            password = data.get('password'),
            name = data.get('name'),
            email_address = data.get('email_address'),
            organisation = data.get('organisation'),
            recipient_country_code = data.get('recipient_country_code'),
            administrator = bool(data.get('administrator'))
            )
        db.session.add(newU)
        db.session.commit()
        setPermission(newU, "domestic_external", data.get("domestic_external"))
        setPermission(newU, "domestic_external_edit", data.get("domestic_external_edit"))
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
            user_id = data["user_id"],
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