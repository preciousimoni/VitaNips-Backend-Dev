from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserProfileView,
    MedicalHistoryViewSet, VaccinationViewSet
)

router = DefaultRouter()
router.register(r'medical-history', MedicalHistoryViewSet, basename='medical-history')
router.register(r'vaccinations', VaccinationViewSet, basename='vaccinations')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('', include(router.urls)),
]