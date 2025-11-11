# notifications/views.py
from rest_framework import generics, viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .models import Notification, NotificationPreference, NotificationDelivery
from .serializers import (
    NotificationSerializer, NotificationPreferenceSerializer,
    NotificationDeliverySerializer
)
from push_notifications.models import APNSDevice, GCMDevice


class NotificationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user notifications
    
    list: Get all notifications for the current user
    retrieve: Get specific notification details
    mark_as_read: Mark notification as read
    mark_all_as_read: Mark all notifications as read
    get_unread_count: Get count of unread notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            dismissed=False
        ).select_related('actor').prefetch_related('deliveries')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(unread=True).update(
            unread=False,
            read_at=timezone.now()
        )
        return Response({'status': f'{updated} notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a notification"""
        notification = self.get_object()
        notification.dismiss()
        return Response({'status': 'notification dismissed'})
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get notifications grouped by category"""
        category = request.query_params.get('category')
        if category:
            notifications = self.get_queryset().filter(category=category)
        else:
            notifications = self.get_queryset()
        
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for the current user's notification preferences.
    
    get: Retrieve notification preferences.
    put: Update notification preferences.
    patch: Partially update notification preferences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj


class DeviceRegistrationView(views.APIView):
    """
    Handles registration of user devices for push notifications.
    Expects POST request with:
    {
        "registration_id": "YOUR_DEVICE_TOKEN_OR_FCM_ID",
        "type": "web" | "ios" | "android"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        registration_id = request.data.get('registration_id')
        device_type = request.data.get('type', '').lower()

        if not registration_id:
            return Response({"error": "registration_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if device_type not in ['web', 'ios', 'android']:
            return Response({"error": "Invalid or missing 'type'. Must be 'web', 'ios', or 'android'."}, status=status.HTTP_400_BAD_REQUEST)

        created = False
        try:
            if device_type == 'ios':
                device, created = APNSDevice.objects.update_or_create(
                    registration_id=registration_id,
                    defaults={'user': user, 'active': True}
                )
            else:
                device, created = GCMDevice.objects.update_or_create(
                    registration_id=registration_id,
                    defaults={'user': user, 'active': True, 'cloud_message_type': 'FCM'}
                )

            action = "registered" if created else "updated"
            return Response(
                {"detail": f"Device {action} successfully."},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error registering device for user {user.id}: {e}")
            return Response({"error": "Failed to register device."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)