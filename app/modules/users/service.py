from app.core.base_service import BaseService
from app.core.extensions import db
from app.modules.auth.model import User
from app.modules.auth.model import UserRole


class UserService(BaseService):
    """
    Service layer for user management operations.
    Used primarily by admin panel for user listing, role management,
    and account administration.

    Inherits from BaseService:
        get_by_id(), get_by_id_or_404(), get_all(),
        paginate(), count(), delete(), save()
    """
    model = User

    @staticmethod
    def get_paginated_users(page: int = 1, per_page: int = 20):
        """
        Return paginated list of all users, newest first.
        Used in admin user management table.
        """
        return (
            User.query
            .order_by(User.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def get_by_email(email: str):
        """
        Fetch a user by email address.
        Used in admin search and auth flows.
        Returns None if not found.
        """
        return User.query.filter_by(
            email=email.strip().lower()
        ).first()

    @staticmethod
    def promote_to_admin(user_id: int) -> User:
        """
        Grant admin role to a user.

        Used by super-admin to elevate trusted users.
        Raises ValueError if user is not found or already admin.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        if user.is_admin:
            raise ValueError(f"{user.name} is already an admin.")

        user.role = UserRole.ADMIN
        db.session.commit()
        return user

    @staticmethod
    def demote_to_user(user_id: int) -> User:
        """
        Revoke admin role from a user, returning them to standard user.
        Raises ValueError if a user is not found or not currently admin.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        if not user.is_admin:
            raise ValueError(f"{user.name} is not an admin.")

        user.role = UserRole.USER
        db.session.commit()
        return user

    @staticmethod
    def toggle_verification(user_id: int) -> User:
        """
        Toggle a user's email verification status.
        Useful for admin to manually verify or unverified accounts.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        user.is_verified = not user.is_verified
        db.session.commit()
        return user

    @staticmethod
    def get_stats() -> dict:
        """
        Return basic user statistics for admin dashboard.
        """
        total = User.query.count()
        verified = User.query.filter_by(is_verified=True).count()
        admins = User.query.filter_by(role=UserRole.ADMIN).count()

        return {
            "total_users": total,
            "verified_users": verified,
            "admin_users": admins,
            "unverified_users": total - verified,
        }
