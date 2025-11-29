# payments/urls.py
from django.urls import path
from .views import InitializePaymentView, VerifyPaymentView, PaymentWebhookView

app_name = 'payments'

urlpatterns = [
    path('initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]

