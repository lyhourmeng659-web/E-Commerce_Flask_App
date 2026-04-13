from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.extensions import db


class UserRole:
    """
    Role constants for user permission levels.
    Using a class instead of Enum keeps string comparison simple
    while centralizing role values to prevent typos.
    """
    USER = "user"
    ADMIN = "admin"


class User(db.Model, UserMixin):
    """
    Core user model. Inherits UserMixin which provides:
        - is_authenticated → True if logged in
        - is_active        → True (overridden below to require verification)
        - is_anonymous     → False for real users
        - get_id()         → returns str(self.id) for session
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default=UserRole.USER)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Email verification
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(255), nullable=True)

    # Session management
    refresh_token = db.Column(db.String(255), nullable=True)

    # Password reset
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    cart_items = db.relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    orders = db.relationship(
        "Order",
        back_populates="user",
        lazy="select",
    )
    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<User {self.email} role={self.role}>"

    # Password

    def set_password(self, password: str) -> None:
        """Hash and store password. Never store or log the raw value."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Constant-time comparison against stored hash."""
        return check_password_hash(self.password_hash, password)

    # Reset token helpers

    def set_reset_token(self, token: str, expires_in_hours: int = 1) -> None:
        """
        Store a password reset token with an expiry timestamp.
        """
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=expires_in_hours)

    def clear_reset_token(self) -> None:
        """
        Consume the reset token after a successful password change.
        Called by AuthService.reset_password() after updating the password.
        """
        self.reset_token = None
        self.reset_token_expiry = None

    def is_reset_token_valid(self) -> bool:
        """
        Check if the stored reset token is still within its expiry window.
        Returns False if token is missing or expired.
        """
        if not self.reset_token or not self.reset_token_expiry:
            return False
        # Use naive UTC now to match what SQLite returns
        now = datetime.utcnow()
        expiry = self.reset_token_expiry
        # Strip tzinfo if present (handles both SQLite naive and other DBs)
        if expiry.tzinfo is not None:
            expiry = expiry.replace(tzinfo=None)
        return now < expiry

    # Role helpers

    @property
    def is_admin(self) -> bool:
        """Property (not method) — consistent with Flask-Login style."""
        return self.role == UserRole.ADMIN

    @property
    def is_active(self) -> bool:
        """
        Override Flask-Login's is_active — ties login access to verification.
        Unverified users are rejected automatically by Flask-Login.
        """
        return self.is_verified

    @property
    def first_name(self) -> str:
        """First word of name for display use."""
        return self.name.split()[0] if self.name else ""
