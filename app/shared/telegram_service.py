import requests
from flask import current_app


def _send_message(text: str) -> bool:
    """
    Core function that sends a message to a Telegram chat via Bot API.

    Args:
        text: HTML-formatted string. Telegram supports:
              <b>bold</b>, <i>italic</i>, <code>code</code>, <a href="">link</a>

    Returns:
        True if delivered, False if config missing or request failed.
        Never raises — all failures are logged and swallowed.
    """
    token   = current_app.config.get("TELEGRAM_BOT_TOKEN")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        current_app.logger.warning(
            "Telegram notification skipped: TELEGRAM_BOT_TOKEN or "
            "TELEGRAM_CHAT_ID not configured in .env"
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id":    chat_id,
                "text":       text,
                "parse_mode": "HTML",
            },
            timeout=5,
        )
        response.raise_for_status()
        return True

    except requests.Timeout:
        current_app.logger.error("Telegram API timed out after 5 seconds.")
        return False
    except requests.HTTPError as e:
        current_app.logger.error(
            f"Telegram API HTTP error: {e.response.status_code} - {e.response.text}"
        )
        return False
    except requests.RequestException as e:
        current_app.logger.error(f"Telegram request failed: {e}")
        return False


# Public alias — support_service.py and other modules import this name
send_telegram_message = _send_message


def send_order_notification(order) -> bool:
    """
    Send new order notification to admin Telegram chat.
    Called by orders/service.py after successful checkout.
    """
    items_lines = [
        f"\n  • {item.product_name} x{item.quantity} — ${item.price:.2f}"
        for item in order.items
    ]
    items_text = "".join(items_lines)

    text = (
        f"<b>🛒 New Order #{order.id}</b>\n\n"
        f"<b>Customer:</b> {order.customer_name}\n"
        f"<b>Email:</b> {order.customer_email}\n"
        f"<b>Address:</b> {order.address}, {order.city}, {order.country}\n"
        f"<b>Payment:</b> {order.payment_method}\n"
        f"<b>Total:</b> ${order.total_amount:.2f}\n\n"
        f"<b>Items:</b>{items_text}"
    )

    return _send_message(text)


def send_support_notification(message) -> bool:
    """
    Send new support message notification to admin Telegram chat.
    Called by support/service.py after message is saved.
    Keeps formatting in one place instead of scattered across services.
    """
    text = (
        f"<b>📩 New Support Message</b>\n\n"
        f"<b>From:</b> {message.name}\n"
        f"<b>Email:</b> {message.email}\n"
        f"<b>Subject:</b> {message.display_subject}\n\n"
        f"<b>Message:</b>\n{message.message[:300]}"
        f"{'...' if len(message.message) > 300 else ''}"
    )

    return _send_message(text)


def send_low_stock_notification(product) -> bool:
    """
    Send low stock alert when product stock drops below the LOW_STOCK_THRESHOLD.
    Called by orders/service.py after stock is decremented on checkout.
    """
    text = (
        f"<b>⚠️ Low Stock Alert</b>\n\n"
        f"<b>Product:</b> {product.title}\n"
        f"<b>Remaining Stock:</b> {product.stock}\n"
        f"<b>Product ID:</b> #{product.id}"
    )

    return _send_message(text)