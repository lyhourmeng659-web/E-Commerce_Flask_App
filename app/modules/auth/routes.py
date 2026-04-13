from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required

from app.modules.auth.service import AuthService
from app.shared.decorators import anonymous_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@anonymous_required
def login():
    """
    GET:  Render login form.
    POST: Validate credentials and log in.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("front/login.html", email=email)

        try:
            AuthService.authenticate(
                {"email": email, "password": password},
                remember=remember,
            )
            flash("Welcome back!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("main.home"))

        except ValueError as e:
            current_app.logger.warning(f"Failed login for: {email}")
            flash(str(e), "danger")
            return render_template("front/login.html", email=email)

    return render_template("front/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@anonymous_required
def register():
    """
    GET:  Render registration form.
    POST: Validate and create user account.
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("front/register.html", name=name, email=email)

        try:
            AuthService.register({
                "name": name,
                "email": email,
                "password": password,
            })
            flash(
                "Account created! Please check your email to verify your account.",
                "success",
            )
            return redirect(url_for("auth.login"))

        except ValueError as e:
            flash(str(e), "danger")
            return render_template("front/register.html", name=name, email=email)

    return render_template("front/register.html")


@auth_bp.get("/verify/<token>")
def verify_email(token: str):
    """
    Consume a one-time verification token and activate the account.
    """
    try:
        AuthService.verify_email(token)
        flash("Email verified! You can now log in.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@anonymous_required
def forgot_password():
    """
    GET:  Show forgot-password form.
    POST: Send reset email if account exists.

    Security: Always show success — never reveal whether email is registered.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Please enter your email address.", "danger")
            return render_template("front/forgot_password.html")

        try:
            AuthService.request_password_reset(email)
        except Exception as e:
            current_app.logger.error(f"Password reset error for {email}: {e}")

        flash(
            "If an account exists for that email, a reset link has been sent. "
            "Check your inbox.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("front/forgot_password.html")


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
@anonymous_required
def reset_password(token: str):
    """
    GET:  Validate token, show new-password form.
    POST: Apply new password, redirect to login.
    """
    if request.method == "GET":
        if not AuthService.is_reset_token_valid(token):
            flash(
                "This reset link is invalid or has expired. "
                "Please request a new one.",
                "danger",
            )
            return redirect(url_for("auth.forgot_password"))
        return render_template("front/reset_password.html", token=token)

    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not password or not confirm:
        flash("Please fill in both password fields.", "danger")
        return render_template("front/reset_password.html", token=token)

    if password != confirm:
        flash("Passwords do not match.", "danger")
        return render_template("front/reset_password.html", token=token)

    try:
        AuthService.reset_password(token, password)
        flash("Password updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("auth.forgot_password"))


@auth_bp.post("/logout")
@login_required
def logout():
    """
    POST-only logout for CSRF safety.
    GET logout is vulnerable — any link can log the user out.
    """
    AuthService.logout(current_user.id)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.post("/refresh")
@login_required
def refresh():
    """Rotate refresh token — returns new token as JSON for API clients."""
    try:
        new_token = AuthService.refresh_token(current_user.id)
        return {"refresh_token": new_token}
    except ValueError as e:
        return {"error": str(e)}, 400
