from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Route decorator that restricts access to admin users only.

    Behavior:
    - Unauthenticated users → redirected to login page with a flash message
    - Authenticated non-admins → 403 Forbidden
    - Authenticated admins → request proceeds normally

    Usage:
        @admin_bp.route("/dashboard")
        @login_required        ← Flask-Login's built-in (handles redirect)
        @admin_required        ← our custom check for admin role
        def dashboard(): ...
    """

    @wraps(f)  # Preserves original function name and docstring
    def decorated(*args, **kwargs):
        # Check authentication first — redirect to log in if not logged in
        # (better UX than showing a 403 to someone who just isn't logged in yet)
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        # Check admin role — authenticated but not admin = forbidden
        if not current_user.is_admin:
            abort(403)

        return f(*args, **kwargs)

    return decorated


def verified_required(f):
    """
    Route decorator that restricts access to users with verified email.

    Behavior:
    - Unauthenticated → redirected to log in
    - Authenticated but unverified → redirected to home with warning flash
    - Verified users → request proceeds normally

    Usage:
        @orders_bp.route("/checkout")
        @login_required
        @verified_required
        def checkout(): ...
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        # Assumes User model has an `is_verified` boolean field
        if not current_user.is_verified:
            flash("Please verify your email before continuing.", "warning")
            return redirect(url_for("main.index"))

        return f(*args, **kwargs)

    return decorated


def anonymous_required(f):
    """
    Route decorator that restricts access to non-authenticated users only.
    Redirects already-logged-in users away from login/register pages.

    Usage:
        @auth_bp.route("/login")
        @anonymous_required
        def login(): ...
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated:
            flash("You are already logged in.", "info")
            return redirect(url_for("main.home"))

        return f(*args, **kwargs)

    return decorated
