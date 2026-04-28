from django.test import SimpleTestCase, override_settings

from .mpesa import format_phone_number, validate_mpesa_config


class MpesaHelpersTests(SimpleTestCase):
    def test_format_phone_number_converts_local_number(self):
        self.assertEqual(format_phone_number("0712345678"), "254712345678")

    def test_format_phone_number_keeps_international_number(self):
        self.assertEqual(format_phone_number("+254712345678"), "254712345678")

    @override_settings(
        MPESA_CONSUMER_KEY="key",
        MPESA_CONSUMER_SECRET="secret",
        MPESA_SHORTCODE="174379",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.ngrok-free.dev/payments/mpesa/callback/",
        MPESA_ENVIRONMENT="sandbox",
    )
    def test_validate_mpesa_config_accepts_valid_callback(self):
        self.assertIsNone(validate_mpesa_config())

    @override_settings(
        MPESA_CONSUMER_KEY="key",
        MPESA_CONSUMER_SECRET="secret",
        MPESA_SHORTCODE="174379",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.ngrok-free.dev/payments/mpesa-callback/",
        MPESA_ENVIRONMENT="sandbox",
    )
    def test_validate_mpesa_config_rejects_wrong_callback_path(self):
        self.assertEqual(
            validate_mpesa_config(),
            "M-Pesa callback URL must end with /payments/mpesa/callback/.",
        )
