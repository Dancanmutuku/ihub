import logging

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


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


def _send_email(subject, message, recipients):
    clean_recipients = [email for email in recipients if email]
    if not clean_recipients:
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=clean_recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send notification email: %s", subject)


def send_order_created_notifications(order):
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


def send_order_status_update_notification(order, previous_status):
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


def send_payment_completed_notifications(payment):
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


def send_payment_failed_notification(payment):
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
