from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.modules.orders.service import OrderService

users_bp = Blueprint("users", __name__, url_prefix="/account")


@users_bp.get("/orders")
@login_required
def order_history():
    """
    Display the current user's full order history, newest first.
    Uses OrderService.get_user_orders() which eager-loads order items.
    """
    orders = OrderService.get_user_orders(current_user.id)
    return render_template("front/order_history.html", orders=orders)
