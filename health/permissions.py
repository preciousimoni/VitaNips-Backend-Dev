# health/permissions.py
from rest_framework import permissions

class IsOwnerOrAssociatedDoctorReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user (for now)
        # Or restrict further: return request.user == obj.user or check doctor link
        # if request.method in permissions.SAFE_METHODS:
        #    # Check if the user is the owner (patient)
        #    if obj.user == request.user:
        #        return True
        #    # FUTURE: Check if user is a doctor associated with the appointment
        #    # if hasattr(request.user, 'doctor_profile') and obj.appointment and obj.appointment.doctor == request.user.doctor_profile:
        #    #     return True
        #    return False # Or True if any logged-in user can view any doc initially? Safer to be False.

        # Write permissions (PUT, PATCH, DELETE) are only allowed to the owner.
        return obj.user == request.user