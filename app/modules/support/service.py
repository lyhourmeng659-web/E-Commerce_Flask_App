"""
Support Service
Handles support message creation and admin management.

Notification trigger wired:
  - notify_support_reply → called after message saved, if user is logged in
"""

from flask import current_app
from flask_login import current_user
from marshmallow import ValidationError

from app.core.extensions import db
from app.modules.support.model import SupportMessage
from app.modules.support.schema import SupportMessageSchema
from app.modules.support.utils import sanitize_message
from app.shared.marshmallow_utils import flatten_errors

support_schema = SupportMessageSchema()


class SupportService:

    @staticmethod
    def create_message(data: dict) -> SupportMessage:
        """
        Validate and save a support message, then send notifications.

        Notifications sent:
          1. Telegram alert to admin (always)
          2. Auto-reply email to user (always)
          3. In-app notification → notify_support_reply (if user is logged in)

        Raises ValueError on validation failure.
        """
        try:
            validated = support_schema.load(data)
        except ValidationError as e:
            raise ValueError(flatten_errors(e.messages))

        subject = validated.get("subject") or "General Inquiry"
        message = SupportMessage(
            name=validated["name"],
            email=validated["email"],
            subject=subject,
            message=sanitize_message(validated["message"]),
        )
        db.session.add(message)
        db.session.commit()

        SupportService._send_notifications(message)
        return message

    @staticmethod
    def _send_notifications(message: SupportMessage) -> None:
        """
        Fire Telegram alert, auto-reply email, and in-app notification.
        All are fire-and-forget — failures logged, never raised.
        """
        # Telegram alert to admin
        try:
            from app.shared.telegram_service import send_support_notification
            send_support_notification(message)
        except Exception as e:
            current_app.logger.error(f"[SUPPORT] Telegram alert failed: {e}")

        # Auto-reply email to user
        try:
            from app.shared.email_service import send_support_reply
            send_support_reply(message)
        except Exception as e:
            current_app.logger.error(f"[SUPPORT] Auto-reply email failed: {e}")

        # In-app notification → notify_support_reply
        try:
            if current_user.is_authenticated:
                from app.modules.notifications.service import NotificationService
                NotificationService.notify_support_reply(current_user.id)
        except Exception as e:
            current_app.logger.error(f"[SUPPORT] notify_support_reply failed: {e}")

    #  Admin helpers

    @staticmethod
    def get_all_messages(unread_only: bool = False):
        query = SupportMessage.query.order_by(SupportMessage.created_at.desc())
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.all()

    @staticmethod
    def get_message_by_id(message_id: int):
        return db.session.get(SupportMessage, message_id)

    @staticmethod
    def mark_as_read(message_id: int) -> None:
        message = db.session.get(SupportMessage, message_id)
        if message and not message.is_read:
            message.is_read = True
            db.session.commit()

    @staticmethod
    def update_status(message_id: int, status: str) -> None:
        valid = {"open", "in_progress", "resolved"}
        if status not in valid:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid)}")
        message = db.session.get(SupportMessage, message_id)
        if not message:
            raise ValueError("Message not found.")
        message.status = status
        db.session.commit()

    @staticmethod
    def get_unread_count() -> int:
        return SupportMessage.query.filter_by(is_read=False).count()
