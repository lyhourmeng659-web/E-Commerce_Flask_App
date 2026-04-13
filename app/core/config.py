import os
from dotenv import load_dotenv

# Load environment variables from .env file into os.environ.
# Must be called before accessing os.environ.get() below.
# In production, environment variables are set on the server directly
# and .env is not present — load_dotenv() safely does nothing in that case.
load_dotenv()

# Path Constants
# BASE_DIR points to the /app directory (one level up from /core).
# Used to build absolute paths for uploads and other file storage.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# instance/ folder sits at project root — SQLite DB stored here
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Create instance/ directory if it doesn't exist
# exist_ok=True prevents error if it already exists
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Absolute path where uploaded product images are stored.
# Kept as a module-level constant so it can be imported independently
# (e.g., in seed.py or CLI scripts) without instantiating the full app.
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/products")

# Allowed image file extensions for upload validation.
from app.shared.constants import ALLOWED_EXTENSIONS


class Config:
    """
    Base configuration class.
    All values are loaded from environment variables via .env file.
    Sensitive defaults are avoided in production — SECRET_KEY will
    raise a warning if not explicitly set.
    """

    # Core Flask

    # SECRET_KEY signs session cookies and CSRF tokens.
    # MUST be set via .env in production — fallback is for dev only.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database

    # SQLite URI for development. Override in ProductionConfig with PostgresSQL.
    # Path is relative to the Flask instance folder by default.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'app.db')}"
    )

    # Disable SQLAlchemy event system — not needed and adds overhead.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File Uploads

    UPLOAD_FOLDER = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS

    # Email (Flask-Mail via Gmail SMTP)

    MAIL_SERVER = "smtp.gmail.com"  # Gmail SMTP server address
    MAIL_PORT = 587  # Port 587 uses STARTTLS encryption
    MAIL_USE_TLS = True  # Upgrade connection to TLS after handshake
    MAIL_USE_SSL = False  # SSL and TLS are mutually exclusive — keep False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")  # Use Gmail App Password, not account password
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")  # "From" address in sent emails

    # Base URL
    # Used to build absolute links in emails (verification, password reset).
    # Set BASE_URL in .env:
    #   Development:  BASE_URL=http://localhost:5000
    #   Production:   BASE_URL=https://yourdomain.com
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

    # Telegram Notifications

    # Used by telegram_service.py to send order/alert notifications.
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


class DevelopmentConfig(Config):
    """
    Development-specific overrides.
    Enables Flask debug mode and detailed SQLAlchemy query logging.
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Prints all SQL queries to console — useful for debugging


class TestingConfig(Config):
    """
    Testing-specific overrides.
    Uses an in-memory SQLite DB so tests never touch the real database.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disable CSRF for form testing


class ProductionConfig(Config):
    """
    Production-specific overrides.
    DEBUG must always be False — never expose stack traces in production.
    DATABASE_URL should point to PostgresSQL or another production DB.
    """
    DEBUG = False
    SQLALCHEMY_ECHO = False


# Config Selector
# Maps environment name strings to config classes.
# Used in create_app() to select config based on FLASK_ENV variable.
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    """
    Returns the appropriate Config class based on the FLASK_ENV
    environment variable. Defaults to DevelopmentConfig if not set.

    Usage in create_app():
        from app.core.config import get_config
        app.config.from_object(get_config())
    """
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
