from sqlalchemy import func
from app.core.extensions import db
from app.modules.auth.model import User
from app.modules.categories.model import Category
from app.modules.orders.model import Order
from app.modules.products.model import Product
from app.shared.constants import OrderStatus, DEFAULT_PAGE, DEFAULT_PER_PAGE


class AdminService:
    """
    Service layer for admin dashboard data aggregation.
    All methods return pre-computed stats and lists ready for template rendering.
    No business logic mutations here — read-only queries only.
    """
    @staticmethod
    def get_dashboard_stats() -> dict:
        """
        Aggregate key business metrics for the admin dashboard overview cards.

        Uses SQL COUNT and SUM directly — more efficient than loading all rows
        into Python and calling len() or sum().

        Returns dict with:
            total_products   (int)   — all products in catalog
            total_categories (int)   — all categories
            total_users      (int)   — all registered users
            total_orders     (int)   — all orders ever placed
            total_revenue    (float) — sum of all completed order totals
            pending_orders   (int)   — orders awaiting processing
            unread_support   (int)   — unread support messages for badge
        """
        # SQL SUM on total_amount for PAID/SHIPPED/DELIVERED orders only
        # Excludes CANCELLED and REFUNDED to show true earned revenue
        revenue = db.session.query(
            func.sum(Order.total_amount)
        ).filter(
            Order.status.in_([
                OrderStatus.PAID,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
            ])
        ).scalar() or 0

        # Count orders still needing admin action
        pending = Order.query.filter_by(
            status=OrderStatus.PENDING
        ).count()

        # Unread support message count for admin notification badge
        from app.modules.support.model import SupportMessage
        unread_support = SupportMessage.query.filter_by(is_read=False).count()

        return {
            "total_products": Product.query.count(),
            "total_categories": Category.query.count(),
            "total_users": User.query.count(),
            "total_orders": Order.query.count(),
            "total_revenue": float(revenue),
            "pending_orders": pending,
            "unread_support": unread_support,
        }

    @staticmethod
    def get_recent_orders(limit: int = 10):
        """
        Return the most recent orders for the admin dashboard activity feed.

        Args:
            limit: Maximum number of orders to return (default 10)

        Returns list of Order objects ordered by newest first.
        Use selectin loading so order. Items are available without extra queries.
        """
        return (
            Order.query
            .order_by(Order.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_orders(status: str = None, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        q = Order.query.order_by(Order.created_at.desc())
        if status:
            q = q.filter_by(status=status)
        return  q.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_recent_users(limit: int = 5):
        """
        Return the most recently registered users.
        Shown in admin dashboard as a 'New Members' panel.
        """
        return (
            User.query
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_users(page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        return User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_all_support(unread_only: bool = False, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        from app.modules.support.model import SupportMessage
        q = SupportMessage.query.order_by(SupportMessage.created_at.desc())
        if unread_only:
            q = q.filter_by(is_read=False)
        return q.paginate(page=page, per_page=per_page, error_out=False)
