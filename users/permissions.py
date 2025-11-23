from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/view it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        # Assuming a patient is a user who is not a doctor or pharmacy staff
        # You might want to refine this logic based on your specific role architecture
        is_doctor = getattr(request.user, 'doctor_profile', None) is not None
        return request.user.is_authenticated and not (is_doctor or request.user.is_pharmacy_staff)

class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'doctor_profile', None) is not None

class IsPharmacy(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_pharmacy_staff

