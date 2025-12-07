# payments/urls.py
from django.urls import path
from .views import InitializePaymentView, VerifyPaymentView, PaymentWebhookView
from .subscription_views import (
    SubscriptionPlanListView,
    UserSubscriptionView,
    SubscribeView,
    CancelSubscriptionView,
    CheckSubscriptionStatusView,
    PharmacySubscriptionView,
    ActivatePharmacySubscriptionView
)
from .premium_feature_views import (
    PremiumFeaturesListView,
    PurchasePremiumFeatureView,
    SubscribePremiumSOSView
)

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Subscription endpoints
    path('subscriptions/plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('subscriptions/current/', UserSubscriptionView.as_view(), name='current-subscription'),
    path('subscriptions/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('subscriptions/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscriptions/status/', CheckSubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscriptions/pharmacy/', PharmacySubscriptionView.as_view(), name='pharmacy-subscription'),
    path('subscriptions/pharmacy/activate/', ActivatePharmacySubscriptionView.as_view(), name='activate-pharmacy-subscription'),
    
    # Premium feature endpoints
    path('premium-features/', PremiumFeaturesListView.as_view(), name='premium-features-list'),
    path('premium-features/purchase/', PurchasePremiumFeatureView.as_view(), name='purchase-premium-feature'),
    path('premium-features/sos/', SubscribePremiumSOSView.as_view(), name='premium-sos-subscription'),
]

