from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app.modules.cart.service import CartService

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.get("/")
@login_required
def cart():
    """
    Display the current user's cart with items, subtotal, shipping, and total.
    CartService.get_details() returns the full structured cart dict.
    """
    return render_template("front/cart.html", cart=CartService.get_details())


@cart_bp.post("/add-to-cart")
@login_required
def add_to_cart():
    """
    Add a product to the cart or increase its quantity if already present.

    After adding, redirects back to the referring page (e.g. product detail)
    so the user continues browsing — only falls back to cart on failure.
    """
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", default=1, type=int)

    if not product_id or quantity <= 0:
        flash("Invalid product data.", "danger")
        return redirect(request.referrer or url_for("products.products_list"))

    try:
        CartService.add_item(product_id, quantity)
        flash("Product added to cart!", "success")
        # Redirect back to where the user came from (product page, category, etc.)
        return redirect(request.referrer or url_for("cart.cart"))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for("cart.cart"))


@cart_bp.post("/update")
@login_required
def update_cart():
    """
    Update the quantity of a cart item.
    Setting quantity to 0 removes the item.
    """
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)

    if not product_id or quantity is None:
        flash("Invalid update request.", "danger")
        return redirect(url_for("cart.cart"))

    try:
        CartService.update_item(product_id, quantity)
        flash("Cart updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("cart.cart"))


@cart_bp.post("/remove")
@login_required
def remove_from_cart():
    """
    Remove a specific product from the cart.
    """
    product_id = request.form.get("product_id", type=int)

    if not product_id:
        flash("Invalid request.", "danger")
        return redirect(url_for("cart.cart"))

    CartService.remove_item(product_id)
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart.cart"))


@cart_bp.post("/clear")
@login_required
def clear_cart_route():
    """
    Clear all items from the current user's cart.
    """
    CartService.clear_cart()
    flash("Your cart has been cleared.", "info")
    return redirect(url_for("cart.cart"))
