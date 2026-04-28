from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.order_create, name='order_create'),
    path('my-orders/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('<int:order_id>/receipt/', views.order_receipt, name='order_receipt'),
    path('<int:order_id>/invoice/', views.order_invoice, name='order_invoice'),
]
