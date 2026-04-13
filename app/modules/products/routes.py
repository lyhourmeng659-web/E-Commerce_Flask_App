from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required
from app.modules.categories.service import CategoryService
from app.modules.products.service import ProductService
from app.shared.decorators import admin_required
from app.shared.constants import DEFAULT_PAGE, FREE_SHIPPING_THRESHOLD

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.get("/")
def products_list():
    """
    Display paginated list of all in-stock products.
    """
    page = request.args.get("page", DEFAULT_PAGE, type=int)
    products = ProductService.get_paginated(page=page)

    if products.pages and page > products.pages:
        return redirect(url_for("products.products_list", page=products.pages))

    return render_template("front/products.html", products=products)


@products_bp.get("/search")
def search_product():
    """
    Search products by keyword across title, description, slug, category.
    Falls back to full paginated listing if no keyword provided.
    """
    page = request.args.get("page", DEFAULT_PAGE, type=int)
    keyword = request.args.get("q", "").strip()

    products = (
        ProductService.search(keyword, page=page)
        if keyword
        else ProductService.get_paginated(page=page)
    )

    return render_template("front/products.html", products=products, keyword=keyword)


@products_bp.get("/<int:product_id>")
def product_detail(product_id: int):
    """
    Display the full product detail page.
    Also fetches related products from the same category.
    """
    product = ProductService.get_by_id(product_id)
    if not product:
        abort(404)

    # Related products — same category, excluding current product, limit 4
    related = (
        ProductService.model.query
        .filter(
            ProductService.model.category_id == product.category_id,
            ProductService.model.id != product_id,
            ProductService.model.stock > 0,
        )
        .limit(4)
        .all()
    )

    return render_template(
        "front/product_details.html",
        product=product,
        related_products=related,
        free_threshold=FREE_SHIPPING_THRESHOLD
    )
