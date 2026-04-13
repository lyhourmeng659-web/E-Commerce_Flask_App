from os import abort

from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from flask_login import login_required, current_user
from pyexpat.errors import messages

from app.modules.notifications.service import NotificationService
from app.modules.notifications.utils import group_notifications_by_date, format_notif_time
from app.modules.notifications.schema import notifications_schema

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


# User Pages

@notifications_bp.route("/")
@login_required
def all_notifications():
    """
    Full notifications page.
    Groups notifications by date (Today / Yesterday / 12 Mar etc.)
    and marks all as read when the user opens the page.
    """
    notifs = NotificationService.get_all_for_user(current_user.id)
    grouped = group_notifications_by_date(notifs)

    # Mark all read as soon as the user opens this page
    NotificationService.mark_all_read(current_user.id)

    return render_template(
        "front/notifications.html",
        grouped_notifications=grouped,
        total=len(notifs),
        format_time=format_notif_time,
    )


# User Actions

@notifications_bp.route("/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id: int):
    """
    Mark a single notification as read.
    Supports both:
      - AJAX: X-Requested-With: XMLHttpRequest → returns JSON {ok: true}
      - Regular POST: redirects back to referrer
    """
    ok = NotificationService.mark_read(notif_id, current_user.id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": ok})

    return redirect(request.referrer or url_for("notifications.all_notifications"))


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read. Redirects back."""
    NotificationService.mark_all_read(current_user.id)
    flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for("notifications.all_notifications"))


@notifications_bp.route("/<int:notif_id>/delete", methods=["POST"])
@login_required
def delete(notif_id: int):
    """Delete a single notification."""
    NotificationService.delete(notif_id, current_user.id)
    return redirect(request.referrer or url_for("notifications.all_notifications"))


@notifications_bp.route("/clear-read", methods=["POST"])
@login_required
def clear_read():
    """Delete all read notifications for the current user."""
    deleted = NotificationService.delete_all_read(current_user.id)
    flash(f"Cleared {deleted} read notification{'s' if deleted != 1 else ''}.", "success")
    return redirect(url_for("notifications.all_notifications"))


# Admin routes
@notifications_bp.route("/admin/broadcast", methods=["POST"])
@login_required
def admin_broadcast():
    """
    Send a promotional notification to ALL users.
    Admin only — returns 403 for non-admin users.

    Form fields:
        title   — short heading (required)
        message — detail text (required)
        link    — optional URL to link to (default: /)

    How it works:
      1. Validate admin role
      2. Read all user IDs from DB
      3. Call NotificationService.notify_promo() for each user
      4. Flash success count and redirect back

    Usage in admin panel — add a form like:
        <form method="POST" action="{{ url_for('notifications.admin_broadcast') }}">
            <input name="title"   placeholder="Promo title" required>
            <input name="message" placeholder="Promo detail" required>
            <input name="link"    placeholder="/products (optional)">
            <button type="submit">Send to All Users</button>
        </form>
    """
    if not current_user.is_admin:
        abort(403)

    title = request.form.get("title", "").strip()
    messages = request.form.get("message", "").strip()
    link = request.form.get("link", "/").strip() or "/"

    if not title or not messages:
        flash("Title and message are required for broadcast.", "danger")
        return redirect(request.referrer or url_for("admin.dashboard"))

    # Import here to avoid circular imports
    from app.modules.auth.model import User
    user_ids = [
        u.id for u in User.query.with_entities(User.id).all()
    ]

    sent = 0
    for uid in user_ids:
        result = NotificationService.notify_promo(
            uid,
            title,
            messages,
            link
        )
        if result is not False:  # notify_promo returns None on succes
            sent += 1

    flash(f"Broadcast sent to {sent} user{'s' if sent != 1 else ''}.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


# API endpoint (AJAX / JSON)

@notifications_bp.route("/api/unread-count")
@login_required
def api_unread_count():
    """
    Returns unread count as JSON.
    Useful for polling the badge count without a full page reload.

    Response: {"count": 3}
    """
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({"count": count})


@notifications_bp.route("/api/recent")
@login_required
def api_recent():
    """
    Returns the 10 most recent notifications as JSON.
    Used to refresh the navbar dropdown via AJAX without reloading the page.

    Response: {"notifications": [...], "unread_count": 2}
    """
    notifs = NotificationService.get_for_user(current_user.id, limit=10)
    unread = NotificationService.get_unread_count(current_user.id)
    data = notifications_schema.dump(notifs)

    # Add formatted time to each notification for display
    for item, n in zip(data, notifs):
        item["time_ago"] = format_notif_time(n.created_at)

    return jsonify({"notifications": data, "unread_count": unread})
