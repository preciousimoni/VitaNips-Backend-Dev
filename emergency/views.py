# emergency/views.py
from rest_framework import generics, views, permissions, status
from rest_framework.response import Response
from .tasks import send_sos_alerts_task
from .models import EmergencyService, EmergencyContact, EmergencyAlert
from .serializers import (
    EmergencyServiceSerializer, EmergencyContactSerializer, EmergencyAlertSerializer
)
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

class TriggerSOSView(views.APIView):
    """
    Receives SOS trigger from frontend, queues background task to send alerts.
    Expects POST data: {'latitude': float, 'longitude': float, 'message': str (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        message = request.data.get('message', None)

        if latitude is None or longitude is None:
            return Response(
                {"error": "Latitude and Longitude are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat_float = float(latitude)
            lon_float = float(longitude)
            if not (-90 <= lat_float <= 90 and -180 <= lon_float <= 180):
                raise ValueError("Invalid latitude or longitude range.")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid latitude or longitude format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            send_sos_alerts_task.delay(
                user_id=request.user.id,
                latitude=lat_float,
                longitude=lon_float,
                message=message
            )
            return Response(
                {"status": "SOS signal received and processing initiated."},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            print(f"ERROR queueing SOS task for user {request.user.id}: {e}")
            return Response(
                {"error": "Could not initiate SOS alert process. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
                user_location = Point(float(longitude), float(latitude), srid=4326)
                radius_km = float(radius_km)
                queryset = queryset.filter(
                    location__distance_lte=(user_location, D(km=radius_km))
                )
            except (ValueError, TypeError) as e:
                print(f"Error processing location parameters: {e}")
                pass

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