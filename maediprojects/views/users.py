from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, \
    current_app
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin,
                            confirm_login,
                            fresh_login_required)
                            
from maediprojects import app, db, models
from maediprojects.query import user as quser
from maediprojects.lib import codelists

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    return quser.user(id)
    
@app.route("/users/")
@login_required
def users():
    users = quser.user()
    return render_template("users.html",
             users = users,
             loggedinuser=current_user)

@app.route("/users/new/", methods=["GET", "POST"])
@login_required
def users_new():
    if request.method=="GET":
        user = {}
        return render_template("user.html",
                 user = user,
                 loggedinuser=current_user,
                 codelists = codelists.get_codelists())
    elif request.method == "POST":
        if quser.addUser(request.form):
            flash("Successfully created user!", "success")
        else:
            flash("Sorry, couldn't create that user!", "danger")
        return redirect(url_for("users"))

@app.route("/users/<user_id>/", methods=["GET", "POST"])
@login_required
def users_edit(user_id):
    if request.method=="GET":
        user = quser.user(user_id)
        return render_template("user.html",
                 user = user,
                 loggedinuser=current_user,
                 codelists = codelists.get_codelists())
    elif request.method == "POST":
        if quser.updateUser(request.form):
            flash("Successfully updated user!", "success")
        else:
            flash("Sorry, couldn't update that user!", "danger")
        return redirect(url_for("users"))

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        user = quser.user_by_username(request.form["username"])
        if (user and user.check_password(request.form["password"])):
            if login_user(user):
                flash("Logged in!", "success")
                if request.args.get("next"):
                    redir_url = request.script_root + request.args.get("next")
                else:
                    redir_url = url_for("dashboard")
                return redirect(redir_url)
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash(u"Invalid username or password.", "danger")
    return render_template("login.html",
             loggedinuser=current_user)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'success')
    redir_url = url_for("dashboard")
    return redirect(redir_url)