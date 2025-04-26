from rest_framework import generics, permissions
from .models import EmergencyService, EmergencyContact, EmergencyAlert
from .serializers import (
    EmergencyServiceSerializer, EmergencyContactSerializer, EmergencyAlertSerializer
)
from haversine import haversine, Unit

class EmergencyServiceListView(generics.ListAPIView):
    serializer_class = EmergencyServiceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = EmergencyService.objects.all()

        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lon')
        radius_km = self.request.query_params.get('radius', default=10)

        if latitude and longitude:
            try:
                user_location = (float(latitude), float(longitude))
                radius_km = float(radius_km)

                # --- Option A: Simple Haversine Filtering ---
                service_ids_in_radius = []
                for service in queryset.filter(latitude__isnull=False, longitude__isnull=False):
                    service_location = (service.latitude, service.longitude)
                    distance = haversine(user_location, service_location, unit=Unit.KILOMETERS)
                    if distance <= radius_km:
                        service_ids_in_radius.append(service.id)
                queryset = queryset.filter(id__in=service_ids_in_radius)

                # --- Option B: GeoDjango Filtering (Requires PostGIS setup) ---
                # See comments in PharmacyListView for GeoDjango example

            except (ValueError, TypeError) as e:
                print(f"Error processing location parameters: {e}") # Log the error
                pass # Ignoring invalid params

        # Add other filters (e.g., by service_type)
        service_type = self.request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        return queryset.order_by('name')

class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

class EmergencyAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmergencyAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyAlert.objects.filter(user=self.request.user)