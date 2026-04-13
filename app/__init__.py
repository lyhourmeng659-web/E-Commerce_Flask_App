import os
from flask import Flask, render_template
from flask_login import current_user

from app.core.config import get_config
from app.core.extensions import db, migrate, login_manager, mail
from app.modules.notifications.service import NotificationService


def create_app() -> Flask:
    """
    Application Factory Pattern.

    Creates and fully configures a Flask application instance.
    Using a factory function (instead of a global app object) allows:
    - Multiple instances for testing (each test gets a fresh app)
    - Different configs per environment (dev/test/prod)
    - Avoids circular imports by deferring blueprint/model imports

    Returns a fully configured Flask app ready to serve requests.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Configuration
    app.config.from_object(get_config())

    # Ensure instance/ folder exists — SQLite creates the .db file here.
    # Must exist BEFORE db.init_app() tries to connect.
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure upload folder exists — prevents errors when saving product images.
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path, "static", "uploads", "products"
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register Models
    _register_models()

    # Initialize Extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # User Loader
    _register_user_loader(app)

    # Register Blueprints
    _register_blueprints(app)

    # Register Error Handlers
    _register_error_handlers(app)

    # Register Context Processors
    _register_context_processors(app)

    return app


# Private Helpers

def _register_models() -> None:
    """
    Import all SQLAlchemy models to populate db before migrations run.
    """
    from app.modules.auth.model import User
    from app.modules.categories.model import Category
    from app.modules.products.model import Product
    from app.modules.wishlist.model import Wishlist
    from app.modules.orders.model import Order, OrderItem
    from app.modules.cart.model import CartItem
    from app.modules.support.model import SupportMessage
    from app.modules.notifications.model import Notification


def _register_user_loader(app: Flask) -> None:
    """
    Register Flask-Login's user_loader callback.

    Called on every authenticated request to reload the User object
    from the DB using the ID stored in the session cookie.
    """
    from app.modules.auth.model import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    """
    Register all feature module blueprints.
    """
    from app.modules.main.routes import main_bp
    from app.modules.auth.routes import auth_bp
    from app.modules.categories.routes import categories_bp
    from app.modules.products.routes import products_bp
    from app.modules.cart.routes import cart_bp
    from app.modules.orders.routes import orders_bp
    from app.modules.wishlist.routes import wishlist_bp
    from app.modules.admin.routes import admin_bp
    from app.modules.support.routes import support_bp
    from app.modules.users.routes import users_bp
    from app.modules.notifications.routes import notifications_bp
    from app.api.health import api_bp

    for blueprint in [
        main_bp, auth_bp, categories_bp, products_bp,
        cart_bp, orders_bp, wishlist_bp, admin_bp,
        support_bp, users_bp, notifications_bp, api_bp,
    ]:
        app.register_blueprint(blueprint)


def _register_context_processors(app: Flask) -> None:
    """
    Inject shared variables into every Jinja2 template automatically.
    """
    from app.modules.cart.service import CartService
    from app.modules.wishlist.service import WishlistService
    from app.modules.categories.service import CategoryService

    @app.context_processor
    def inject_globals() -> dict:
        cart_count = 0
        wishlist_count = 0
        wishlist_ids = set()
        notif_count = 0
        navbar_notifications = []

        if current_user.is_authenticated:
            try:
                cart_count = CartService.get_cart_count()
                wishlist_count = WishlistService.count()
                wishlist_ids = WishlistService.get_wishlist_ids()
                notif_count = NotificationService.get_unread_count(current_user.id)
                navbar_notifications = NotificationService.get_for_user(current_user.id, limit=10)
            except Exception:
                pass

        try:
            all_categories = CategoryService.get_all_nav()
        except Exception:
            all_categories = []

        return dict(
            cart_count=cart_count,
            wishlist_count=wishlist_count,
            wishlist_ids=wishlist_ids,
            all_categories=all_categories,
            notif_count=notif_count,
            navbar_notifications=navbar_notifications,
        )


def _register_error_handlers(app: Flask) -> None:
    """
    Register custom error pages for 403, 404, and unhandled exceptions (500).
    """

    @app.errorhandler(403)
    def forbidden(error):
        """Triggered by abort(403) — admin_required decorator."""
        return render_template("error/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        """Triggered by abort(404) or unmatched URL."""
        return render_template("error/404.html"), 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        """
        Catch-all for unhandled exceptions.

        Rolls back any open DB transaction to prevent dirty writes
        from persisting on the next request using the same connection.
        Log the full traceback server-side for debugging.

        NOTE: If home.html or master.html have Jinja syntax errors,
        this handler itself will fail trying to render 500.html —
        fix all template syntax errors first before relying on this.
        """
        from flask import current_app
        current_app.logger.exception(f"Unhandled exception: {error}")
        db.session.rollback()
        return render_template("error/500.html"), 500
