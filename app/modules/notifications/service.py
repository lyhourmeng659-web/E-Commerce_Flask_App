from app.core.extensions import db
from app.modules.notifications.model import Notification
from app.modules.notifications.utils import get_icon


class NotificationService:
    """
    Central service for creating and managing user notifications.

    All public notify_* methods are the preferred way to create notifications
    from other parts of the app. They use get_icon() from utils.py so icon
    strings are never hardcoded in callers.

    Quick usage from any module:
        from app.modules.notifications.service import NotificationService
        NotificationService.notify_welcome(user.id)
        NotificationService.notify_order_placed(user.id, order.order_number, order.id)
        NotificationService.notify_password_changed(user.id)
    """

    # Read

    @staticmethod
    def get_for_user(user_id: int, limit: int = 10) -> list:
        """
        Return the most recent `limit` notifications for a user.
        Used by the context processor to populate the navbar dropdown.
        Default limit=10 keeps the dropdown short.
        """
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_for_user(user_id: int) -> list:
        """
        Return ALL notifications for the full /notifications page.
        No limit — caller should paginate if needed.
        """
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """
        Return the number of unread notifications.
        Called on every request via the context processor — kept fast
        by the index on (user_id, is_read).
        """
        return (
            Notification.query
            .filter_by(user_id=user_id, is_read=False)
            .count()
        )

    # Core create

    @staticmethod
    def create(
        user_id:  int,
        title:    str,
        message:  str,
        link:     str = None,
        icon:     str = "bi-bell",
    ) -> "Notification | None":
        """
        Create and persist a single notification.

        Always wraps in try/except — a notification failure must NEVER
        break the main request that triggered it.
        Returns the Notification on success, None on failure.
        """
        try:
            n = Notification(
                user_id = user_id,
                title   = title,
                message = message,
                link    = link,
                icon    = icon,
            )
            db.session.add(n)
            db.session.commit()
            return n
        except Exception as exc:
            db.session.rollback()
            _log_error(f"Failed to create notification for user {user_id}: {exc}")
            return None

    # Predefined event notifications
    # Wire these into auth_service.py, orders/service.py, admin routes, etc.
    # Each method documents exactly WHERE in the app it should be called.

    @staticmethod
    def notify_welcome(user_id: int) -> None:
        """
        Call this in: auth/service.py → verify_email(), after account activated.

            user.is_verified = True
            db.session.commit()
            NotificationService.notify_welcome(user.id)   ← add this line
        """
        NotificationService.create(
            user_id = user_id,
            title   = "Welcome! Your account is ready.",
            message = "Your email has been verified. You can now browse and shop.",
            link    = "/",
            icon    = get_icon("welcome"),
        )

    @staticmethod
    def notify_email_verified(user_id: int) -> None:
        """Alias for notify_welcome — use either, they produce the same result."""
        NotificationService.notify_welcome(user_id)

    @staticmethod
    def notify_order_placed(user_id: int, order_number: str, order_id: int) -> None:
        """
        Call this in: orders/service.py → place_order(), after db.session.commit().

            order = Order(...)
            db.session.commit()
            NotificationService.notify_order_placed(   ← add this
                user.id, order.order_number, order.id
            )
        """
        NotificationService.create(
            user_id = user_id,
            title   = f"Order #{order_number} confirmed",
            message = "We've received your order and it's being processed.",
            link    = "/account/orders",
            icon    = get_icon("order_placed"),
        )

    @staticmethod
    def notify_order_shipped(user_id: int, order_number: str) -> None:
        """
        Call this in: admin/routes.py → when admin updates order status to 'shipped'.

            order.status = "shipped"
            db.session.commit()
            NotificationService.notify_order_shipped(order.user_id, order.order_number)
        """
        NotificationService.create(
            user_id = user_id,
            title   = f"Order #{order_number} is on its way!",
            message = "Your order has been shipped and is heading to you.",
            link    = "/account/orders",
            icon    = get_icon("order_shipped"),
        )

    @staticmethod
    def notify_order_delivered(user_id: int, order_number: str) -> None:
        """
        Call this in: admin/routes.py → when order status updated to 'delivered'.
        """
        NotificationService.create(
            user_id = user_id,
            title   = f"Order #{order_number} delivered",
            message = "Your order has been delivered. Enjoy your purchase!",
            link    = "/account/orders",
            icon    = get_icon("order_delivered"),
        )

    @staticmethod
    def notify_order_cancelled(user_id: int, order_number: str) -> None:
        """
        Call this in: orders/service.py or admin → when order is canceled.
        """
        NotificationService.create(
            user_id = user_id,
            title   = f"Order #{order_number} cancelled",
            message = "Your order has been cancelled. Contact support if you need help.",
            link    = "/support",
            icon    = get_icon("order_cancelled"),
        )

    @staticmethod
    def notify_password_changed(user_id: int) -> None:
        """
        Call this in: auth/service.py → reset_password(), after db.session.commit().

            user.set_password(new_password)
            db.session.commit()
            NotificationService.notify_password_changed(user.id)   ← add this
        """
        NotificationService.create(
            user_id = user_id,
            title   = "Password changed",
            message = "Your password was updated. If this wasn't you, contact support immediately.",
            link    = "/support",
            icon    = get_icon("password_changed"),
        )

    @staticmethod
    def notify_support_reply(user_id: int) -> None:
        """
        Call this in: support/service.py → after a support reply is sent.
        """
        NotificationService.create(
            user_id = user_id,
            title   = "Support reply received",
            message = "We've responded to your support request. Check your email.",
            link    = "/support",
            icon    = get_icon("support_reply"),
        )

    @staticmethod
    def notify_promo(user_id: int, title: str, message: str, link: str = "/") -> None:
        """
        Generic promotional notification. Used by admin to broadcast deals.
        """
        NotificationService.create(
            user_id = user_id,
            title   = title,
            message = message,
            link    = link,
            icon    = get_icon("promo"),
        )

    # Mark read

    @staticmethod
    def mark_read(notif_id: int, user_id: int) -> bool:
        """
        Mark a single notification as read.
        Always checks user_id to prevent one user reading another's notifications.
        Returns True on success, False if not found or wrong user.
        """
        n = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
        if not n:
            return False
        n.is_read = True
        db.session.commit()
        return True

    @staticmethod
    def mark_all_read(user_id: int) -> int:
        """
        Mark all unread notifications as read for a user.
        Returns the number of rows updated.
        """
        updated = (
            Notification.query
            .filter_by(user_id=user_id, is_read=False)
            .update({"is_read": True})
        )
        db.session.commit()
        return updated

    # Delete

    @staticmethod
    def delete(notif_id: int, user_id: int) -> bool:
        """
        Delete a single notification.
        Verifies ownership — user can only delete their own notifications.
        """
        n = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
        if not n:
            return False
        db.session.delete(n)
        db.session.commit()
        return True

    @staticmethod
    def delete_all_read(user_id: int) -> int:
        """
        Delete all read notifications for a user.
        Returns the number of rows deleted.
        Used by the "Clear Read" button on the notifications page.
        """
        deleted = (
            Notification.query
            .filter_by(user_id=user_id, is_read=True)
            .delete()
        )
        db.session.commit()
        return deleted


# Private helpers

def _log_error(msg: str) -> None:
    """Safe logger — works inside and outside app context."""
    try:
        from flask import current_app
        current_app.logger.error(f"[NOTIF] {msg}")
    except RuntimeError:
        print(f"[NOTIF ERROR] {msg}")