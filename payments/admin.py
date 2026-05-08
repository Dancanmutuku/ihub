from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_reference', 'phone_number', 'amount', 'status', 'mpesa_receipt_number', 'created']
    list_filter = ['status']
    search_fields = ['mpesa_receipt_number', 'phone_number', 'order__id']
    readonly_fields = ['raw_callback', 'created', 'updated']
    list_select_related = ['order']

    def order_reference(self, obj):
        if obj.order_id:
            return f'Order #{obj.order_id}'
        return 'Missing order'

    order_reference.short_description = 'Order'
