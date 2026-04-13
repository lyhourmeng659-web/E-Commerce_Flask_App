from flask import render_template, current_app
from flask_mail import Message
from app.core.extensions import mail


def _send_email(subject: str, recipients: list, template: str, **kwargs) -> bool:
    """
    Base function for sending HTML emails via Flask-Mail.

    All public send_* functions call this internally.
    Returns True on success, False on failure — never raises.
    Email failure should never break a user-facing request.
    """
    try:
        msg = Message(subject=subject, recipients=recipients)
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        current_app.logger.info(f"Email sent to {recipients}: {subject}")
        return True

    except Exception as e:
        current_app.logger.error(f"Email failed to {recipients} — {subject}: {e}")
        return False


def send_order_confirmation(order) -> bool:
    """
    Send order confirmation email to the customer after successful checkout.
    Renders templates/email/invoice.html with the order object.
    """
    return _send_email(
        subject=f"Order Confirmation #{order.order_number or order.id}",
        recipients=[order.customer_email],
        template="email/invoice.html",
        order=order,
    )


def send_welcome_email(user, verify_url: str = None) -> bool:
    """
    Send a welcome + email verification email to a newly registered user.

    If verify_url is not provided, falls back to a message asking
    the user to check the terminal (development fallback).

    Renders templates/email/welcome.html with user and verify_url.
    """
    return _send_email(
        subject="Welcome — Please Verify Your Email",
        recipients=[user.email],
        template="email/welcome.html",
        user=user,
        verify_url=verify_url,
    )


def send_password_reset_email(user, reset_url: str) -> bool:
    """
    Send a password reset link to the user.
    reset_url is a tokenized absolute URL built in AuthService._send_reset_email().
    Renders templates/email/password_reset.html with user and reset_url.
    """
    return _send_email(
        subject="Reset Your Password",
        recipients=[user.email],
        template="email/password_reset.html",
        user=user,
        reset_url=reset_url,
    )


def send_support_reply(message) -> bool:
    """
    Send auto-reply email to user after they submit a support message.
    Renders templates/email/support_reply.html with the message object.
    """
    return _send_email(
        subject=f"We received your message — {message.display_subject}",
        recipients=[message.email],
        template="email/support_reply.html",
        message=message,
    )
