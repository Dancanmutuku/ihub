from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.test import TestCase, override_settings

from payments.models import Payment
from store.models import Category, Product

from .models import Order, OrderItem
from .notifications import _send_email


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="store@example.com",
    ADMIN_NOTIFICATION_EMAILS=["admin@example.com"],
    ASYNC_EMAIL_NOTIFICATIONS=False,
    BREVO_API_KEY="",
)
class OrderPaymentNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="secret123",
            first_name="Alice",
            last_name="Wanjiru",
        )
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.product = Product.objects.create(
            category=self.category,
            name="ThinkPad X1",
            slug="thinkpad-x1",
            description="Business laptop",
            price=Decimal("125000.00"),
            stock=5,
        )

    def create_order(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Alice",
            last_name="Wanjiru",
            email="checkout@example.com",
            phone="0712345678",
            address="123 Moi Avenue",
            city="Nairobi",
            county="Nairobi",
            postal_code="00100",
            notes="Call on arrival",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            price=Decimal("125000.00"),
            quantity=1,
        )
        return order

    def seed_cart(self):
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
                "name": self.product.name,
                "image_url": self.product.image_url,
                "slug": self.product.slug,
            }
        }
        session.save()

    def test_order_creation_notifies_customer_and_admin(self):
        self.client.force_login(self.user)
        self.seed_cart()

        response = self.client.post(
            reverse("orders:order_create"),
            data={
                "first_name": "Alice",
                "last_name": "Wanjiru",
                "email": "checkout@example.com",
                "phone": "0712345678",
                "address": "123 Moi Avenue",
                "city": "Nairobi",
                "county": "Nairobi",
                "postal_code": "00100",
                "notes": "Call on arrival",
            },
        )

        order = Order.objects.latest("id")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(f"Order #{order.id} received", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertEqual(mail.outbox[1].to, ["admin@example.com"])

    def test_anonymous_user_must_sign_in_before_checkout(self):
        response = self.client.get(reverse("orders:order_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response.url)

    def test_order_status_update_notifies_customer(self):
        order = self.create_order()
        mail.outbox = []

        order.status = "shipped"
        order.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Order #{order.id} is now shipped", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])

    def test_payment_completed_notifies_customer_and_admin(self):
        order = self.create_order()
        payment = Payment.objects.create(
            order=order,
            phone_number="0712345678",
            amount=Decimal("125000.00"),
            status="pending",
        )
        mail.outbox = []

        payment.status = "completed"
        payment.mpesa_receipt_number = "QWE123XYZ"
        payment.save()

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(f"Payment received for order #{order.id}", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertEqual(mail.outbox[1].to, ["admin@example.com"])

    def test_payment_failed_notifies_customer(self):
        order = self.create_order()
        payment = Payment.objects.create(
            order=order,
            phone_number="0712345678",
            amount=Decimal("125000.00"),
            status="pending",
        )
        mail.outbox = []

        payment.status = "failed"
        payment.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Payment failed for order #{order.id}", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])

    def test_paid_customer_can_open_receipt(self):
        order = self.create_order()
        order.paid = True
        order.mpesa_code = "ABC123XYZ"
        order.save(update_fields=["paid", "mpesa_code"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("orders:order_receipt", args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Receipt")
        self.assertContains(response, "TECHSTORE")
        self.assertContains(response, "ABC123XYZ")

    def test_unpaid_customer_receipt_redirects_to_order(self):
        order = self.create_order()
        self.client.force_login(self.user)

        response = self.client.get(reverse("orders:order_receipt", args=[order.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("orders:order_detail", args=[order.id]), response.url)

    def test_staff_can_open_invoice(self):
        order = self.create_order()
        staff = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="secret123",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("orders:order_invoice", args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Client Invoice")
        self.assertContains(response, f"INV-{order.id:06d}")

    @override_settings(
        BREVO_API_KEY="brevo-test-key",
        DEFAULT_FROM_EMAIL="TechStore KE <sender@example.com>",
    )
    @patch("orders.notifications.requests.post")
    def test_brevo_api_is_used_when_key_exists(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None

        _send_email("Subject", "Body text", ["alice@example.com"])

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["api-key"], "brevo-test-key")
        self.assertEqual(kwargs["json"]["sender"]["email"], "sender@example.com")
        self.assertEqual(kwargs["json"]["to"][0]["email"], "alice@example.com")
