# doctors/permissions.py
from rest_framework import permissions
from .models import Appointment

class IsDoctorUser(permissions.BasePermission):
    """
    Allows access only to users who have a doctor profile.
    """
    message = "You do not have a doctor profile."
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'doctor_profile') and request.user.doctor_profile is not None

class IsDoctorAssociatedWithAppointment(permissions.BasePermission):
    """
    Object-level permission to only allow doctors to access appointments
    they are associated with.
    """
    message = "You are not authorized to manage prescriptions for this appointment."
    def has_object_permission(self, request, view, obj):
        # obj is an Appointment instance here
        if not hasattr(request.user, 'doctor_profile') or request.user.doctor_profile is None:
            return False
        return obj.doctor == request.user.doctor_profile

class IsPrescribingDoctor(permissions.BasePermission):
    """
    Object-level permission to only allow doctors to access prescriptions
    they have created or are associated with.
    """
    message = "You are not authorized to manage this prescription."
    def has_object_permission(self, request, view, obj):
        # obj is a Prescription instance here
        if not hasattr(request.user, 'doctor_profile') or request.user.doctor_profile is None:
            return False
        return obj.doctor == request.user.doctor_profile