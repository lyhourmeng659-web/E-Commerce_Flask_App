from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from app.modules.support.service import SupportService

support_bp = Blueprint("support", __name__, url_prefix="/support")


@support_bp.route("/", methods=["GET", "POST"])
def support():
    """
    GET:  Render contact form, pre-filling fields if user is authenticated.
    POST: Validate and save support message, send notifications, redirect.
    """
    # Pre-fill form values for logged-in users
    # Falls back to empty string for guests
    prefill = {
        "name": current_user.name if current_user.is_authenticated else "",
        "email": current_user.email if current_user.is_authenticated else "",
        "subject": "",
        "message": "",
    }

    if request.method == "POST":
        # Collect form data — preserves values for re-render on error
        form_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "subject": request.form.get("subject", ""),
            "message": request.form.get("message", ""),
        }

        try:
            SupportService.create_message(form_data)
            flash(
                "Your message has been sent! We'll get back to you soon.",
                "success"
            )
            # PRG pattern: redirect after successful POST prevents re-submission
            return redirect(url_for("support.support"))

        except Exception as e:
            flash(str(e), "danger")
            return render_template(
                "front/support.html",
                form=form_data,
            )

    return render_template("front/support.html", form=prefill)
