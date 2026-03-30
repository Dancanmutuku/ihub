import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from orders.models import Order
from .models import Payment
from .mpesa import stk_push


def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'No active order found.')
        return redirect('store:home')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        amount = order.get_total_cost()

        # Initiate STK Push
        result = stk_push(phone_number=phone, amount=amount, order_id=order.id)

        if result['success']:
            Payment.objects.update_or_create(
                order=order,
                defaults={
                    'checkout_request_id': result.get('checkout_request_id', ''),
                    'merchant_request_id': result.get('merchant_request_id', ''),
                    'phone_number': phone,
                    'amount': amount,
                    'status': 'pending',
                }
            )
            messages.success(request, '✅ STK Push sent! Check your phone and enter your M-Pesa PIN.')
            return render(request, 'payments/waiting.html', {'order': order, 'phone': phone})
        else:
            messages.error(request, f'Payment initiation failed: {result.get("error", "Unknown error")}')

    return render(request, 'payments/payment.html', {'order': order})


@require_POST
def check_payment_status(request, order_id):
    """AJAX endpoint for frontend polling."""
    order = get_object_or_404(Order, id=order_id)
    try:
        payment = order.payment
        return JsonResponse({
            'status': payment.status,
            'paid': order.paid,
            'receipt': payment.mpesa_receipt_number,
        })
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'pending', 'paid': False})


@csrf_exempt
def mpesa_callback(request):
    """Safaricom calls this URL after STK Push completes."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk = data.get('Body', {}).get('stkCallback', {})
            checkout_request_id = stk.get('CheckoutRequestID', '')
            result_code = stk.get('ResultCode')

            try:
                payment = Payment.objects.get(checkout_request_id=checkout_request_id)
                payment.raw_callback = data

                if result_code == 0:
                    # Success – extract receipt
                    items = stk.get('CallbackMetadata', {}).get('Item', [])
                    receipt = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), '')
                    payment.mpesa_receipt_number = receipt
                    payment.status = 'completed'
                    order = payment.order
                    order.paid = True
                    order.mpesa_code = receipt
                    order.status = 'processing'
                    order.save()
                else:
                    payment.status = 'failed'

                payment.save()
            except Payment.DoesNotExist:
                pass

        except (json.JSONDecodeError, KeyError):
            pass

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
