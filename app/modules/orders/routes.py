from fileinput import filename
from alembic.util import status
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user
from app.modules.orders.service import OrderService
from app.modules.cart.service import CartService
from app.modules.orders.utils import validate_checkout_data

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required  # Guests must log in before checkout
def checkout():
    """
    GET:  Show checkout form with current cart summary in the sidebar.
    POST: Validate form, create order, send notifications, redirect to success.

    Cart is always loaded first — redirects to cart if empty.
    All validation is handled by validate_checkout_data() and OrderService,
    keeping this route clean and focused on HTTP concerns only.
    """
    cart = CartService.get_details()

    if not cart.get("items"):
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.cart"))

    if request.method == "POST":
        try:
            # validate_checkout_data strips, validates, builds customer_name
            cleaned = validate_checkout_data(request.form)

            order = OrderService.create_order(cleaned)

            flash(
                f"Order #{order.order_number} placed successfully! "
                f"A confirmation has been sent to {order.customer_email}.",
                "success"
            )
            return redirect(url_for("orders.success", order_id=order.id))

        except ValueError as e:
            flash(str(e), "danger")
            return render_template("front/checkout.html", cart=cart)

    return render_template("front/checkout.html", cart=cart)


@orders_bp.get("/success/<int:order_id>")
@login_required
def success(order_id: int):
    """
    Order success / confirmation page shown after checkout.
    Renders a web-friendly order summary — NOT the email invoice template.

    Security: verifies the order belongs to the current user
    so users can't view each other's order confirmations by guessing IDs.
    """
    order = OrderService.get_by_id_or_404(order_id)

    # Prevent users from viewing other users' order confirmations
    if order.user_id != current_user.id:
        abort(403)

    return render_template("front/order_success.html", order=order)


@orders_bp.get("/history")
@login_required
def order_history():
    """
    Show all past orders for the currently logged-in user.
    """
    orders = OrderService.get_user_orders(current_user.id)
    return render_template("front/order_history.html", orders=orders)


@orders_bp.get("/<int:order_id>/invoice")
@login_required
def download_invoice(order_id: int):
    """
    Generate and stream a PDF invoice for the given order.

    How it works:
      1. Fetch the order — 404 if not found
      2. Verify ownership — 403 if wrong user
      3. Check order is not canceled — redirect back if it is
      4. Generate PDF bytes from invoice.html via WeasyPrint
      5. Return as a downloadable PDF file

    The file is named: invoice-ORD-XXXXXXXX.pdf
    Content-Disposition: attachment forces the browser to download
    rather than display inline.

    Security:
      - @login_required: guests cannot download invoices
      - ownership check: users can only download their own invoices
      - canceled orders: no invoice generated (order never fulfilled)
    """
    order = OrderService.get_by_id_or_404(order_id)

    # Ownership check prevent users accessing other users's invoices
    # Admins bypass this check and can download any order's invoice
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    # No invoice for canceled orders
    if order.status == "cancelled":
        flash("Invoice is not available for cancelled orders.", "warning")
        return redirect(url_for("orders.order_history"))

    try:
        from app.modules.orders.pdf import generate_invoice_pdf
        pdf_bytes = generate_invoice_pdf(order)

    except RuntimeError as e:
        flash("Could not generate invoice. Please try again later.", "danger")
        from flask import current_app
        current_app.logger.error(f"[INVOICE] {e}")
        return redirect(url_for("orders.order_history"))

    filename = f"invoice-{order.order_number}.pdf"

    return Response(
        pdf_bytes,
        status=200,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(pdf_bytes)),
        },
    )
