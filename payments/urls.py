from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_process, name='payment_process'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('status/<int:order_id>/', views.check_payment_status, name='check_status'),
]
