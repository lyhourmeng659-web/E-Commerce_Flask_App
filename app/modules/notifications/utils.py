from datetime import datetime
from collections import OrderedDict


# Icon map

NOTIFICATION_ICONS = {
    "welcome":          "bi-person-check",
    "order_placed":     "bi-bag-check",
    "order_shipped":    "bi-truck",
    "order_cancelled":  "bi-x-circle",
    "order_delivered":  "bi-box-seam",
    "password_changed": "bi-shield-lock",
    "password_reset":   "bi-key",
    "email_verified":   "bi-envelope-check",
    "support_reply":    "bi-chat-dots",
    "promo":            "bi-tag",
    "alert":            "bi-exclamation-triangle",
    "info":             "bi-info-circle",
}


def get_icon(event_type: str) -> str:
    """Return Bootstrap Icons class for a given event type. Falls back to bi-bell."""
    return NOTIFICATION_ICONS.get(event_type, "bi-bell")


# Time formatting

def _day_month(dt: datetime, include_year: bool = False) -> str:
    """
    Format a datetime as '9 Mar' or '9 Mar 2025'.
    """
    if include_year:
        return f"{dt.day} {dt.strftime('%b %Y')}"
    return f"{dt.day} {dt.strftime('%b')}"


def format_notif_time(dt: datetime) -> str:
    """
    Return a human-friendly relative time string.

    Examples:
        "Just now"       — under 60 seconds ago
        "5 minutes ago"  — under 1 hour
        "3 hours ago"    — under 24 hours
        "Yesterday"      — 24–48 hours ago
        "9 Mar"          — older, same year
        "9 Mar 2025"     — different year
    """
    now   = datetime.utcnow()
    delta = now - dt
    secs  = int(delta.total_seconds())

    if secs < 60:
        return "Just now"
    if secs < 3600:
        mins = secs // 60
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if secs < 86400:
        hrs = secs // 3600
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    if secs < 172800:
        return "Yesterday"

    return _day_month(dt, include_year=(dt.year != now.year))


# Grouping

def group_notifications_by_date(notifications: list) -> dict:
    """
    Group a flat list of Notification objects into an OrderedDict by date label.

    Returns:
        {
            "Today":     [Notification, ...],
            "Yesterday": [Notification, ...],
            "9 Mar":     [Notification, ...],
        }
    """
    now    = datetime.utcnow().date()
    groups = OrderedDict()

    for n in notifications:
        date  = n.created_at.date()
        delta = (now - date).days

        if delta == 0:
            label = "Today"
        elif delta == 1:
            label = "Yesterday"
        else:
            label = _day_month(
                datetime.combine(date, datetime.min.time()),
                include_year=(date.year != now.year),
            )

        groups.setdefault(label, []).append(n)

    return groups