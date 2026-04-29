import logging
from concurrent.futures import ThreadPoolExecutor
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import close_old_connections, transaction

from .models import Order
from payments.models import Payment


logger = logging.getLogger(__name__)
email_executor = ThreadPoolExecutor(max_workers=4)


def _order_total(order):
    return f"KES {order.get_total_cost():,.2f}"


def _item_summary(order):
    return "\n".join(
        f"- {item.quantity} x {item.product_name} @ KES {item.price:,.2f}"
        for item in order.items.all()
    ) or "- No items recorded"


def _customer_email(order):
    if order.user and order.user.email:
        return order.user.email
    return order.email


def _admin_emails():
    return list(getattr(settings, "ADMIN_NOTIFICATION_EMAILS", []))


def _sender_payload():
    sender_name, sender_email = parseaddr(settings.DEFAULT_FROM_EMAIL)
    return {
        "name": sender_name or "TechStore KE",
        "email": sender_email or settings.DEFAULT_FROM_EMAIL,
    }


def _recipient_payload(recipients):
    return [{"email": email} for email in recipients if email]


def _run_async(task, *args):
    if getattr(settings, "ASYNC_EMAIL_NOTIFICATIONS", True):
        email_executor.submit(_run_with_connection_cleanup, task, *args)
    else:
        task(*args)


def _run_with_connection_cleanup(task, *args):
    close_old_connections()
    try:
        task(*args)
    finally:
        close_old_connections()


def _enqueue(task, *args, on_commit=False):
    async_enabled = getattr(settings, "ASYNC_EMAIL_NOTIFICATIONS", True)
    if on_commit and async_enabled:
        transaction.on_commit(lambda: _run_async(task, *args))
    else:
        _run_async(task, *args)


def _send_email(subject, message, recipients):
    clean_recipients = [email for email in recipients if email]
    if not clean_recipients:
        return

    try:
        if getattr(settings, "BREVO_API_KEY", ""):
            response = requests.post(
                settings.BREVO_API_URL,
                headers={
                    "accept": "application/json",
                    "api-key": settings.BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={
                    "sender": _sender_payload(),
                    "to": _recipient_payload(clean_recipients),
                    "subject": subject,
                    "textContent": message,
                },
                timeout=30,
            )
            response.raise_for_status()
            return

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=clean_recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send notification email: %s", subject)


def _send_order_created_notifications(order_id):
    order = Order.objects.prefetch_related("items").select_related("user").get(pk=order_id)
    customer_subject = f"TechStore KE: Order #{order.id} received"
    customer_message = (
        f"Hello {order.full_name},\n\n"
        f"We have received your order #{order.id} and it is currently marked as {order.status}.\n"
        f"Order total: {_order_total(order)}\n"
        f"Payment method: {order.payment_method.upper()}\n\n"
        "Items ordered:\n"
        f"{_item_summary(order)}\n\n"
        "Delivery details:\n"
        f"{order.address}\n{order.city}, {order.county}\n"
        f"Phone: {order.phone}\n\n"
        "We will email you again when payment is confirmed or your order status changes.\n\n"
        "Thank you for shopping with TechStore KE."
    )
    _send_email(customer_subject, customer_message, [_customer_email(order)])

    admin_subject = f"New order received: #{order.id} ({order.status})"
    admin_message = (
        f"A new order has been placed on TechStore KE.\n\n"
        f"Order ID: #{order.id}\n"
        f"Customer: {order.full_name}\n"
        f"Customer email: {_customer_email(order)}\n"
        f"Phone: {order.phone}\n"
        f"Status: {order.status}\n"
        f"Paid: {'Yes' if order.paid else 'No'}\n"
        f"Order total: {_order_total(order)}\n"
        f"County: {order.county}\n"
        f"Address: {order.address}\n\n"
        "Items:\n"
        f"{_item_summary(order)}\n\n"
        f"Customer notes: {order.notes or 'None'}"
    )
    _send_email(admin_subject, admin_message, _admin_emails())


def send_order_created_notifications(order_id, on_commit=False):
    _enqueue(_send_order_created_notifications, order_id, on_commit=on_commit)


def _send_order_status_update_notification(order_id, previous_status):
    order = Order.objects.select_related("user").get(pk=order_id)
    subject = f"TechStore KE: Order #{order.id} is now {order.status}"
    message = (
        f"Hello {order.full_name},\n\n"
        f"Your order #{order.id} has been updated from {previous_status} to {order.status}.\n"
        f"Order total: {_order_total(order)}\n"
        f"Payment status: {'Paid' if order.paid else 'Pending payment'}\n"
    )

    if order.status == "shipped":
        message += "\nYour package is on the way."
    elif order.status == "delivered":
        message += "\nYour order has been delivered. Enjoy your purchase."
    elif order.status == "cancelled":
        message += "\nThis order has been cancelled. Reach out if you need help."
    else:
        message += "\nWe will keep you updated as your order moves forward."

    message += "\n\nThank you for choosing TechStore KE."
    _send_email(subject, message, [_customer_email(order)])


def send_order_status_update_notification(order_id, previous_status, on_commit=False):
    _enqueue(_send_order_status_update_notification, order_id, previous_status, on_commit=on_commit)


def _send_payment_completed_notifications(payment_id):
    payment = Payment.objects.select_related("order__user").get(pk=payment_id)
    order = payment.order
    receipt = payment.mpesa_receipt_number or "Pending receipt number"

    customer_subject = f"TechStore KE: Payment received for order #{order.id}"
    customer_message = (
        f"Hello {order.full_name},\n\n"
        f"We have received your M-Pesa payment for order #{order.id}.\n"
        f"Amount: KES {payment.amount:,.2f}\n"
        f"M-Pesa receipt: {receipt}\n"
        f"Order status: {order.status}\n\n"
        "Your order is now being prepared, and we will update you again when its status changes.\n\n"
        "Thank you for shopping with TechStore KE."
    )
    _send_email(customer_subject, customer_message, [_customer_email(order)])

    admin_subject = f"Payment received for order #{order.id}"
    admin_message = (
        f"A payment has been received on TechStore KE.\n\n"
        f"Order ID: #{order.id}\n"
        f"Customer: {order.full_name}\n"
        f"Customer email: {_customer_email(order)}\n"
        f"Amount: KES {payment.amount:,.2f}\n"
        f"M-Pesa receipt: {receipt}\n"
        f"Payment status: {payment.status}\n"
        f"Order status: {order.status}"
    )
    _send_email(admin_subject, admin_message, _admin_emails())


def send_payment_completed_notifications(payment_id, on_commit=False):
    _enqueue(_send_payment_completed_notifications, payment_id, on_commit=on_commit)


def _send_payment_failed_notification(payment_id):
    payment = Payment.objects.select_related("order__user").get(pk=payment_id)
    order = payment.order
    subject = f"TechStore KE: Payment failed for order #{order.id}"
    message = (
        f"Hello {order.full_name},\n\n"
        f"We were not able to complete the M-Pesa payment for order #{order.id}.\n"
        f"Attempted amount: KES {payment.amount:,.2f}\n"
        f"Payment status: {payment.status}\n\n"
        "Please try again from the payment page. If money was deducted and you do not get confirmation, contact support with your order number.\n\n"
        "Thank you,\nTechStore KE"
    )
    _send_email(subject, message, [_customer_email(order)])


def send_payment_failed_notification(payment_id, on_commit=False):
    _enqueue(_send_payment_failed_notification, payment_id, on_commit=on_commit)
