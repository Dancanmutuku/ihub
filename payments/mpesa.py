import base64
import requests
from datetime import datetime
from django.conf import settings


# =========================================================
# GET MPESA ACCESS TOKEN
# =========================================================
def get_mpesa_access_token():
    """
    Obtain OAuth access token from Safaricom API
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if settings.MPESA_ENVIRONMENT == "production":
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    credentials = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {credentials}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        print("TOKEN STATUS:", response.status_code)
        print("TOKEN RESPONSE:", response.text)

        response.raise_for_status()

        data = response.json()
        return data.get("access_token")

    except requests.RequestException as e:
        print("M-Pesa token error:", str(e))
        return None


# =========================================================
# GENERATE STK PASSWORD
# =========================================================
def generate_password(shortcode, passkey, timestamp):
    """
    Generate base64 encoded password required by STK Push
    """
    data = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data.encode()).decode("utf-8")


# =========================================================
# NORMALIZE PHONE NUMBER
# =========================================================
def format_phone_number(phone):
    """
    Convert:
    07XXXXXXXX -> 2547XXXXXXXX
    +2547XXXXXXX -> 2547XXXXXXX
    """
    phone = str(phone).strip().replace(" ", "").replace("-", "")

    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    return phone


# =========================================================
# STK PUSH REQUEST
# =========================================================
def stk_push(phone_number, amount, order_id):
    """
    Initiate M-Pesa STK Push payment
    """

    access_token = get_mpesa_access_token()
    if not access_token:
        return {
            "success": False,
            "error": "Failed to obtain access token"
        }

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    callback_url = settings.MPESA_CALLBACK_URL

    password = generate_password(shortcode, passkey, timestamp)
    phone = format_phone_number(phone_number)

    # Select API environment
    if settings.MPESA_ENVIRONMENT == "production":
        url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    else:
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": f"TechStore-{order_id}",
        "TransactionDesc": f"TechStore Order #{order_id}",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        # ================= DEBUG =================
        print("MPESA STK STATUS:", response.status_code)
        print("MPESA STK RESPONSE:", response.text)
        # =========================================

        response.raise_for_status()

        data = response.json()

        if data.get("ResponseCode") == "0":
            return {
                "success": True,
                "checkout_request_id": data.get("CheckoutRequestID"),
                "merchant_request_id": data.get("MerchantRequestID"),
            }

        return {
            "success": False,
            "error": data.get(
                "errorMessage",
                data.get("ResponseDescription", "Unknown error")
            ),
        }

    except requests.RequestException as e:
        print("STK Push error:", str(e))
        return {
            "success": False,
            "error": str(e),
        }