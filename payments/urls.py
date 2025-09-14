"""
URL configuration for payments app.
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Web views
    path('', views.PaymentsView.as_view(), name='payments'),
    path('methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
]
