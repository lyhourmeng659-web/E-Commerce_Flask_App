from flask import Blueprint, render_template
from app.modules.products.service import ProductService

main_bp = Blueprint('main', __name__)


@main_bp.get("/")
@main_bp.get("/home")
def home():
    """
    Home page — renders hero slider, featured products, and category grid.
    """
    products = ProductService.get_featured(limit=8)
    return render_template("front/home.html", products=products)


@main_bp.get("/test-500")
def test_500():
    """
    DEV ONLY — intentionally raises ZeroDivisionError to test
    the @app.errorhandler(Exception) handler and 500.html template.
    Remove or protect with DEBUG guard before deploying to production.
    """
    return 1 / 0
