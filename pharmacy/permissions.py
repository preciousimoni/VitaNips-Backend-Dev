# pharmacy/permissions.py
from rest_framework import permissions

class IsPharmacyStaffOfOrderPharmacy(permissions.BasePermission):
    message = "You do not have permission to access orders for this pharmacy."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_pharmacy_staff

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'works_at_pharmacy') or not request.user.works_at_pharmacy:
            return False
        return obj.pharmacy == request.user.works_at_pharmacy