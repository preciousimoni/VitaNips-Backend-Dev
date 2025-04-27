# pharmacy/permissions.py
from rest_framework import permissions

class IsPharmacyStaffOfOrderPharmacy(permissions.BasePermission):
    """
    Allows access only to pharmacy staff members associated with the
    pharmacy linked to the specific MedicationOrder instance.
    """
    message = "You do not have permission to access orders for this pharmacy."

    def has_permission(self, request, view):
        # Basic check: Must be authenticated and marked as pharmacy staff
        return request.user and request.user.is_authenticated and request.user.is_pharmacy_staff

    def has_object_permission(self, request, view, obj):
        # Instance-level check: User must work at the order's pharmacy
        # Assumes the 'obj' being checked is a MedicationOrder instance
        if not hasattr(request.user, 'works_at_pharmacy') or not request.user.works_at_pharmacy:
            return False # Staff member not linked to any pharmacy
        # Check if user's pharmacy matches the order's pharmacy
        return obj.pharmacy == request.user.works_at_pharmacy