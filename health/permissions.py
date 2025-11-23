from rest_framework import permissions
from django.utils import timezone
from .sharing_models import DocumentShare

class IsOwnerOrSharedWith(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Owner has full access
        if obj.user == request.user:
            return True
        
        # Check if document is shared with user
        if request.method in permissions.SAFE_METHODS:
            return DocumentShare.objects.filter(
                document=obj,
                shared_with=request.user,
                expires_at__gt=timezone.now()
            ).exists() or DocumentShare.objects.filter(
                document=obj,
                shared_with=request.user,
                expires_at__isnull=True
            ).exists()
            
        return False
