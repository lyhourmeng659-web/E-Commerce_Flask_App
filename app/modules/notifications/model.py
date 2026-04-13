from datetime import datetime
from app.core.extensions import db


class Notification(db.Model):
    """
    Per-user notification record.

    Notifications are created by the app (on order placed, order shipped,
    welcome, password reset, etc.) and displayed in the navbar bell dropdown.

    Fields:
        user_id     — owner of this notification
        title       — short bold heading shown in the dropdown
        message     — supporting detail text
        link        — optional URL the notification links to (e.g. order page)
        icon        — Bootstrap Icons class, e.g. 'bi-bag-check', 'bi-shield-lock'
        is_read     — False until user views/marks it read
        created_at  — timestamp for display and sorting
    """
    __tablename__ = "notifications"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title      = db.Column(db.String(120), nullable=False)
    message    = db.Column(db.String(500), nullable=False)
    link       = db.Column(db.String(255), nullable=True)
    icon       = db.Column(db.String(60),  nullable=True,  default="bi-bell")
    is_read    = db.Column(db.Boolean,     nullable=False, default=False)
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # Relationship back to user (lazy load)
    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Notification {self.id} user={self.user_id} read={self.is_read} '{self.title}'>"