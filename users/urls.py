# users/urls.py
from django.urls import path
from .views import (
    UserListView, UserRegistrationView, UserProfileView,
    MedicalHistoryListCreateView, MedicalHistoryDetailView,
    VaccinationListCreateView, VaccinationDetailView
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('medical-history/', MedicalHistoryListCreateView.as_view(), name='medical-history-list'),
    path('medical-history/<int:pk>/', MedicalHistoryDetailView.as_view(), name='medical-history-detail'),
    path('vaccinations/', VaccinationListCreateView.as_view(), name='vaccination-list'),
    path('vaccinations/<int:pk>/', VaccinationDetailView.as_view(), name='vaccination-detail'),
]