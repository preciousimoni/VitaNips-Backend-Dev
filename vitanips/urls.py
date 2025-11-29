# vitanips/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from users.views import UserRegistrationView

app_name = 'vitanips'

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/register/', UserRegistrationView.as_view(), name='auth_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints for each app
    path('api/users/', include('users.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('api/health/', include('health.urls')),
    path('api/insurance/', include('insurance.urls')),
    path('api/emergency/', include('emergency.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/admin/', include('vitanips.core.admin_urls')),
    path('api/payments/', include('payments.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)