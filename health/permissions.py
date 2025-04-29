# health/permissions.py
from rest_framework import permissions

class IsOwnerOrAssociatedDoctorReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
           if obj.user == request.user:
               return True
           if hasattr(request.user, 'doctor_profile') and obj.appointment and obj.appointment.doctor == request.user.doctor_profile:
               return True
           return False

        return obj.user == request.user