from flask import Blueprint, render_template, abort, request, redirect, url_for
from app.modules.categories.service import CategoryService
from app.shared.constants import DEFAULT_PAGE

categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/categories",
)


# Public Routes

@categories_bp.get("/")
def categories_list():
    """
    Display paginated list of all categories.
    Redirects to the last valid page if the requested page exceeds total.
    """
    page = request.args.get("page", DEFAULT_PAGE, type=int)
    categories = CategoryService.get_paginated(page=page)

    # Guard against out-of-range page numbers in URL (e.g. ?page=999)
    if categories.pages and page > categories.pages:
        return redirect(url_for("categories.categories_list", page=categories.pages))

    return render_template("front/categories.html", categories=categories)


@categories_bp.get("/<slug>")
def category_detail(slug: str):
    """
    Display a single category and its paginated products.
    Fetches products via service (paginated) rather than passing
    the relationship directly — prevents loading all products at once.
    """
    category = CategoryService.get_by_slug(slug)
    if not category:
        abort(404)

    page = request.args.get("page", DEFAULT_PAGE, type=int)
    # Paginated products — consistent with the rest of app, avoids memory issues
    products = CategoryService.get_paginated_products(category, page=page)

    return render_template(
        "front/category_detail.html",
        category=category,
        products=products,
    )
