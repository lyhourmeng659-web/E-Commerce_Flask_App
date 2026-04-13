from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager

# Database
# SQLAlchemy ORM instance. Created without app context here (lazy init pattern).
# Bound to the app later via db.init_app(app) in create_app().
# Provides: db.session, db.Model, db.Column, relationships, etc.
db = SQLAlchemy()

# Migrations
# Flask-Migrate wraps Alembic to handle schema versioning.
# Enables: flask db init / flask db migrate / flask db upgrade
# Bound to app and db via migrate.init_app(app, db) in create_app().
migrate = Migrate()

# Email
# Flask-Mail instance for sending transactional emails (order confirmations, etc.)
# Configured via MAIL_* keys in Config class.
# Bound to app via mail.init_app(app) in create_app().
mail = Mail()

# Authentication
# Flask-Login manages user sessions across requests.
# Tracks who is logged in via session cookies.
login_manager = LoginManager()

# The endpoint name to redirect to when @login_required is triggered
# and the user is not authenticated. Maps to auth blueprint's login route.
login_manager.login_view = "auth.login"

# Flash message shown when a user is redirected to log in.
# Displayed in the template via: get_flashed_messages(with_categories=True)
login_manager.login_message = "Please log in to access this page."

# Bootstrap/Tailwind alert category for the flash message above.
# "warning" renders as a yellow alert in most UI frameworks.
login_manager.login_message_category = "warning"
