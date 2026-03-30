from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'phone_number', 'amount', 'status', 'mpesa_receipt_number', 'created']
    list_filter = ['status']
    search_fields = ['mpesa_receipt_number', 'phone_number', 'order__id']
    readonly_fields = ['raw_callback', 'created', 'updated']
