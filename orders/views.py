from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.utils import timezone
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm
from .notifications import send_order_created_notifications


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

    context = {
        'document_type': 'Payment Receipt',
        'document_code': f'RCPT-{order.id:06d}',
        'order': order,
        'generated_at': timezone.localtime(timezone.now()),
    }
    return render(request, 'orders/document.html', context)


@staff_member_required
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'document_type': 'Client Invoice',
        'document_code': f'INV-{order.id:06d}',
        'order': order,
        'generated_at': timezone.localtime(timezone.now()),
    }
    return render(request, 'orders/document.html', context)
