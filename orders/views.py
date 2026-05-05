from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm
from .notifications import send_order_created_notifications


SELLER_DETAILS = {
    'business_name': 'TechStore KE',
    'address': 'Nairobi, Kenya',
    'phone': '+254 726 263 888',
    'email': 'support@techstore.co.ke',
    'payment_terms': 'Due in 7 days',
    'payment_methods': 'M-Pesa 0726263888, Bank 1234567812345678',
    'notes': 'Warranty and return policy apply according to TechStore KE terms. Keep this document for service, returns, and payment reference.',
}


def build_document_context(order, document_kind):
    generated_at = timezone.localtime(timezone.now())
    issue_date = timezone.localtime(order.created)
    due_date = issue_date + timedelta(days=7)
    total = order.get_total_cost()
    payment = getattr(order, 'payment', None)

    if document_kind == 'receipt':
        amount_paid = payment.amount if payment else total
        payment_date = timezone.localtime(payment.updated) if payment else generated_at
        transaction_reference = (
            order.mpesa_code
            or (payment.mpesa_receipt_number if payment else '')
            or 'Recorded payment'
        )
        balance_remaining = max(total - amount_paid, Decimal('0.00'))
        return {
            'document_kind': 'receipt',
            'document_type': 'Payment Receipt',
            'document_code': f'RCPT-{order.id:06d}',
            'invoice_reference': f'INV-{order.id:06d}',
            'order': order,
            'payment': payment,
            'seller': SELLER_DETAILS,
            'generated_at': generated_at,
            'issue_date': issue_date,
            'payment_date': payment_date,
            'transaction_reference': transaction_reference,
            'amount_paid': amount_paid,
            'balance_remaining': balance_remaining,
            'subtotal': total,
            'discount': 0,
            'tax_label': 'VAT',
            'tax_amount': 0,
            'total': total,
            'confirmation_statement': 'Payment received and confirmed. This receipt is proof of payment for the items listed below.',
        }

    return {
        'document_kind': 'invoice',
        'document_type': 'Invoice',
        'document_code': f'INV-{order.id:06d}',
        'order': order,
        'seller': SELLER_DETAILS,
        'generated_at': generated_at,
        'issue_date': issue_date,
        'due_date': due_date,
        'subtotal': total,
        'discount': 0,
        'tax_label': 'VAT',
        'tax_amount': 0,
        'total': total,
        'amount_due': total,
        'confirmation_statement': 'This invoice is a request for payment for the goods listed below. Please use the payment methods shown and quote the invoice number when paying.',
    }


@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

    form = OrderCreateForm(user=request.user)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        product_name=item['product'].name,
                        price=item['price'],
                        quantity=item['quantity'],
                    )
                send_order_created_notifications(order.id, on_commit=True)
            cart.clear()
            request.session['order_id'] = order.id
            return redirect('payments:payment_process')

    return render(request, 'orders/checkout.html', {'cart': cart, 'form': form})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.paid:
        messages.warning(request, 'Receipt is available after payment is confirmed.')
        return redirect('orders:order_detail', order_id=order.id)

    return render(request, 'orders/document.html', build_document_context(order, 'receipt'))


@staff_member_required
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/document.html', build_document_context(order, 'invoice'))
