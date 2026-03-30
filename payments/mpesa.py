import base64
import requests
from datetime import datetime
from django.conf import settings


def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if settings.MPESA_ENVIRONMENT == 'production':
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    credentials = base64.b64encode(f'{consumer_key}:{consumer_secret}'.encode()).decode('utf-8')
    headers = {'Authorization': f'Basic {credentials}'}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.RequestException as e:
        print(f'M-Pesa token error: {e}')
        return None


def generate_password(shortcode, passkey, timestamp):
    data_to_encode = f'{shortcode}{passkey}{timestamp}'
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')


def stk_push(phone_number, amount, order_id):
    """Initiate an M-Pesa STK Push payment."""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'success': False, 'error': 'Could not obtain access token'}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    password = generate_password(shortcode, passkey, timestamp)

    # Normalize phone: 07XXXXXXXX → 2547XXXXXXXX
    phone = str(phone_number).strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]

    if settings.MPESA_ENVIRONMENT == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(float(amount)),
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': f'TechStore-{order_id}',
        'TransactionDesc': f'TechStore Order #{order_id}',
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        if data.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
            }
        return {'success': False, 'error': data.get('errorMessage', data.get('ResponseDescription', 'Unknown error'))}
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}
