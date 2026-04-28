from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'phone', 'status', 'paid', 'get_total_cost', 'invoice_link', 'created']
    list_filter = ['status', 'paid', 'created']
    list_editable = ['status', 'paid']
    search_fields = ['first_name', 'last_name', 'email', 'mpesa_code']
    readonly_fields = ['created', 'updated', 'invoice_link']
    inlines = [OrderItemInline]

    def invoice_link(self, obj):
        url = reverse('orders:order_invoice', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">Open Invoice</a>', url)

    invoice_link.short_description = 'Invoice'
