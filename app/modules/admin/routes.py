from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.modules.admin.service import AdminService
from app.modules.categories.model import Category
from app.modules.products.service import ProductService
from app.modules.categories.service import CategoryService
from app.modules.orders.service import OrderService
from app.modules.users.service import UserService
from app.modules.support.service import SupportService
from app.shared.decorators import admin_required
from app.shared.constants import OrderStatus

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ORDER_STATUSES = ["PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"]


@admin_bp.get("/dashboard")
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard — central hub for business metrics and activity.

    Passes to template:
        stats            (dict)  — counts, revenue, pending orders
        low_stock        (list)  — products below LOW_STOCK_THRESHOLD
        recent_orders    (list)  — last 10 orders placed
        recent_users     (list)  — last 5 registered users

    Using **stats unpacks the dict as individual template variables:
        total_products, total_categories, total_users,
        total_orders, total_revenue, pending_orders, unread_support
    """
    stats = AdminService.get_dashboard_stats()
    low_stock = ProductService.get_low_stock_products()
    recent_orders = AdminService.get_recent_orders(limit=10)
    recent_users = AdminService.get_recent_users(limit=5)

    return render_template(
        "admin/dashboard.html",
        low_stock_products=low_stock,
        recent_orders=recent_orders,
        recent_users=recent_users,
        order_statuses=ORDER_STATUSES,
        **stats,
    )


# Orders
@admin_bp.get("/orders")
@login_required
@admin_required
def orders():
    status = request.args.get("status", "").strip() or None
    page = request.args.get("page", 1, type=int)
    pagination = AdminService.get_all_orders(status=status, page=page)

    return render_template(
        "admin/orders/orders.html",
        pagination=pagination,
        orders=pagination.items,
        current_status=status,
        order_statuses=ORDER_STATUSES
    )


# Order Details
@admin_bp.get("/orders/<int:order_id>")
@login_required
@admin_required
def order_detail(order_id: int):
    order = OrderService.get_by_id_or_404(order_id)
    return render_template(
        "admin/orders/order_detail.html",
        order=order,
        order_statuses=ORDER_STATUSES
    )


# Update Orders
@admin_bp.post("/orders/<int:order_id>/update-status")
@login_required
@admin_required
def update_order_status(order_id: int):
    """
    Update order status → auto-fires customer in-app notification:
        shipped   → "Your order is on its way!"
        delivered → "Your order has been delivered!"
        canceled → "Your order has been canceled."
    Handled by OrderService._trigger_status_notification()
    """
    new_status = request.form.get("status", "").strip()
    if not new_status:
        flash("Please select a status.", "danger")
        return redirect(url_for("admin.order_detail", order_id=order_id))
    try:
        order = OrderService.update_status(order_id, new_status)
        flash(f"Order #{order.order_number} -> '{new_status.replace('_', ' ').title()}'.", "success")
        return redirect(url_for("admin.orders"))
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.order_detail", order_id=order_id))


# Products
@admin_bp.get("/products")
@login_required
@admin_required
def products():
    page = request.args.get("page", 1, type=int)
    pagination = ProductService.get_paginated(page=page, per_page=20)
    return render_template(
        "admin/products/products.html",
        pagination=pagination,
        products=pagination.items
    )


# Create Product
@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_product():
    categories = CategoryService.get_all_nav()
    if request.method == "POST":
        try:
            product = ProductService.create(request.form, request.files.get("image"))
            flash(f"Product '{product.title}' Created.", "success")
            return redirect(url_for("admin.products"))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template("admin/products/product_form.html", product=None, categories=categories)


# Edit Product
@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id: int):
    from app.modules.products.model import Product
    from app.core.extensions import db
    product = db.session.get(Product, product_id) or abort(404)
    categories = CategoryService.get_all_nav()
    if request.method == "POST":
        try:
            ProductService.update(product_id, request.form, request.files.get("image"))
            flash(f"Product '{product.title}' updated.", "success")
            return redirect(url_for("admin.products"))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template("admin/products/product_form.html", product=product, categories=categories)


# Delete Product
@admin_bp.post("/products/<int:product_id>/delete")
@login_required
@admin_required
def delete_product(product_id: int):
    try:
        ProductService.delete(product_id)
        flash("Product deleted.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.products"))


# Categories
@admin_bp.get("/categories")
@login_required
@admin_required
def categories():
    all_cats = CategoryService.get_all_nav()
    return render_template("admin/categories/categories.html", categories=all_cats)


# Create Category
@admin_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_category():
    if request.method == "POST":
        try:
            cat = CategoryService.create(request.form)
            flash(f"Category '{cat.name}' created.", "success")
            return redirect(url_for("admin.categories"))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template("admin/categories/category_form.html", category=None)


# Edit Category
@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(category_id: int):
    from app.modules.categories.model import Category
    from app.core.extensions import db
    category = db.session.get(Category, category_id) or abort(404)
    if request.method == "POST":
        try:
            CategoryService.update(category_id, request.form)
            flash(f"Category updated.", "success")
            return redirect(url_for("admin.categories"))
        except ValueError as e:
            flash(str(e), "danger")
    return render_template("admin/categories/category_form.html", category=category)


# Delete Category
@admin_bp.post("/categories/<int:category_id>/delete")
@login_required
@admin_required
def delete_category(category_id: int):
    try:
        CategoryService.delete(category_id)
        flash("Category deleted.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.categories"))


# Users
@admin_bp.get("/users")
@login_required
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    pagination = AdminService.get_all_users(page=page)
    user_stats = UserService.get_stats()
    return render_template(
        "admin/users/users.html",
        pagination=pagination,
        users=pagination.items,
        **user_stats
    )


# Promote User
@admin_bp.post("/users/<int:user_id>/promote")
@login_required
@admin_required
def promote_user(user_id: int):
    try:
        user = UserService.promote_to_admin(user_id)
        flash(f"{user.name} is now an admin.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.users"))


# Demote User
@admin_bp.post("/users/<int:user_id>/demote")
@login_required
@admin_required
def demote_user(user_id: int):
    if user_id == current_user.id:
        flash("You cannot demote yourself.", "danger")
        return redirect(url_for("admin.users"))
    try:
        user = UserService.demote_to_user(user_id)
        flash(f"{user.name} demote to regular user.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.users"))


# Toggle Verify
@admin_bp.post("/users/<int:user_id>/toggle-verify")
@login_required
@admin_required
def toggle_verify_user(user_id: int):
    try:
        user = UserService.toggle_verification(user_id)
        state = "verified" if user.is_verified else "unverified"
        flash(f"{user.name} is now {state}.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.users"))


# Support
@admin_bp.get("/support")
@login_required
@admin_required
def support():
    unread_only = request.args.get("unread", "0") == "1"
    page = request.args.get("page", 1, type=int)
    pagination = AdminService.get_all_support(unread_only=unread_only, page=page)
    return render_template(
        "admin/supports/supports.html",
        pagination=pagination,
        messages=pagination.items,
        unread_only=unread_only,
        unread_count=SupportService.get_unread_count()
    )


# Support Detail
@admin_bp.get("/support/<int:message_id>")
@login_required
@admin_required
def support_detail(message_id: int):
    message = SupportService.get_message_by_id(message_id) or abort(404)
    SupportService.mark_as_read(message_id)
    return render_template(
        "admin/supports/support_detail.html",
        message=message
    )


# Update Support Status
@admin_bp.post("/support/<int:message_id>/update-status")
@login_required
@admin_required
def update_support_status(message_id: int):
    status = request.form.get("status", "").strip()
    try:
        SupportService.update_status(message_id, status)
        flash(f"Marked as '{status.replace('_', ' ').title()}'.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.support_detail", message_id=message_id))


# Broadcast
@admin_bp.post("/broadcast")
@login_required
@admin_required
def broadcast():
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    link = request.form.get("link", "/").strip() or "/"
    if not title or not message:
        flash("Title and message are required.", "danger")
        return redirect(url_for("admin.dashboard"))
    from app.modules.auth.model import User
    from app.modules.notifications.service import NotificationService
    user_ids = [
        u.id for u in User.query.with_entities(User.id).all()
    ]
    for uid in user_ids:
        NotificationService.notify_promo(uid, title, message, link)
    flash(f"Broadcast sent to {len(user_ids)} users.", "success")
    return redirect(url_for("admin.dashboard"))
