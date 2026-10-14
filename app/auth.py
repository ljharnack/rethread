"""Account routes: register, log in, log out."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .forms import LoginForm, RegisterForm
from .models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            form.username.errors.append("That username is taken.")
        elif User.query.filter_by(email=form.email.data.lower()).first():
            form.email.errors.append("An account with that email already exists.")
        else:
            user = User(username=form.username.data, email=form.email.data.lower())
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to ReThread!", "success")
            return redirect(url_for("shop.index"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_url = request.args.get("next")
            # Only follow relative redirects, so ?next= can't send users to another site.
            if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("shop.index")
            return redirect(next_url)
        flash("Incorrect username or password.", "error")
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("shop.index"))
