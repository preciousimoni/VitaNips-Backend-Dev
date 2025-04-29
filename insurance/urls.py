# insurance/urls.py
from django.urls import path
from .views import (
    InsuranceProviderListView, InsurancePlanListView,
    UserInsuranceListCreateView, UserInsuranceDetailView,
    InsuranceClaimListCreateView, InsuranceClaimDetailView,
    InsuranceDocumentListCreateView, InsuranceDocumentDetailView
)

urlpatterns = [
    path('providers/', InsuranceProviderListView.as_view(), name='insurance-provider-list'),
    path('plans/', InsurancePlanListView.as_view(), name='insurance-plan-list'),
    path('user-insurance/', UserInsuranceListCreateView.as_view(), name='user-insurance-list'),
    path('user-insurance/<int:pk>/', UserInsuranceDetailView.as_view(), name='user-insurance-detail'),
    path('claims/', InsuranceClaimListCreateView.as_view(), name='insurance-claim-list'),
    path('claims/<int:pk>/', InsuranceClaimDetailView.as_view(), name='insurance-claim-detail'),
    path('documents/', InsuranceDocumentListCreateView.as_view(), name='insurance-document-list'),
    path('documents/<int:pk>/', InsuranceDocumentDetailView.as_view(), name='insurance-document-detail'),
]