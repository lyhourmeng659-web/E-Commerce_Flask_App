from datetime import datetime, timezone
from app.core.extensions import db


class SupportMessage(db.Model):
    __tablename__ = "support_messages"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)

    # Indexed for admin filtering by sender email
    email = db.Column(db.String(120), nullable=False, index=True)

    # subject nullable=True — form makes it optional with a sensible default
    subject = db.Column(db.String(200), nullable=True)

    message = db.Column(db.Text, nullable=False)

    # Track whether admin has read the message
    # Shown as unread badge count in admin dashboard
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Track resolution state — useful for admin workflow
    # Values: "open", "in_progress", "resolved"
    status = db.Column(
        db.String(50),
        nullable=False,
        default="open",
        index=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return f"<SupportMessage from={self.email} status={self.status}>"

    @property
    def display_subject(self) -> str:
        """
        Returns subject if provided, or a sensible fallback.
        Prevents empty subject from breaking admin list views.
        """
        return self.subject or "No Subject"
