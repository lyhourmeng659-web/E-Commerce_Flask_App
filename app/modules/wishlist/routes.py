from flask import Blueprint, redirect, request, url_for, render_template, flash
from flask_login import login_required
from app.modules.wishlist.service import WishlistService

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")


@wishlist_bp.post("/add/<int:product_id>")
@login_required
def add(product_id: int):
    """
    Add a product to the current user's wishlist.

    Redirects back to the referring page (product card, detail page, etc.)
    so the user stays in context after adding.
    """
    added = WishlistService.add(product_id)

    if added:
        flash("Added to your wishlist.", "success")
    else:
        flash("Already in your wishlist.", "info")

    return redirect(request.referrer or url_for("products.products_list"))


@wishlist_bp.post("/remove/<int:product_id>")
@login_required
def remove(product_id: int):
    """
    Remove a product from the current user's wishlist.
    """
    removed = WishlistService.remove(product_id)

    if removed:
        flash("Removed from your wishlist.", "info")

    # If removing from the wishlist page, stay there
    # If removing from a product card, go back to that page
    return redirect(request.referrer or url_for("wishlist.view"))


@wishlist_bp.get("/")
@login_required
def view():
    """
    Display the current user's wishlist page.
    Loads all wishlist items with products and categories eagerly.
    """
    items = WishlistService.get_all()
    return render_template("front/wishlist.html", items=items)
