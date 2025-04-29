# doctors/views.py
import datetime
from django.conf import settings
from rest_framework import generics, permissions, filters, views, status
from django.urls import reverse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from notifications.utils import create_notification
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription
from .serializers import (
    SpecialtySerializer, DoctorSerializer, DoctorReviewSerializer,
    DoctorAvailabilitySerializer, AppointmentSerializer, PrescriptionSerializer
)

class SpecialtyListView(generics.ListAPIView):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [permissions.AllowAny]

class DoctorListView(generics.ListAPIView):
    queryset = Doctor.objects.filter(is_verified=True)
    serializer_class = DoctorSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['specialties', 'is_available_for_virtual']
    search_fields = ['first_name', 'last_name', 'bio']

class DoctorDetailView(generics.RetrieveAPIView):
    queryset = Doctor.objects.filter(is_verified=True)
    serializer_class = DoctorSerializer
    permission_classes = [permissions.AllowAny]

class DoctorReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = DoctorReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DoctorReview.objects.filter(doctor_id=self.kwargs['doctor_id'])

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, doctor_id=self.kwargs['doctor_id'])

class DoctorAvailabilityListView(generics.ListAPIView):
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DoctorAvailability.objects.filter(doctor_id=self.kwargs['doctor_id'], is_available=True)

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated] # Add IsOwnerOrAssociatedDoctor later

    def get_queryset(self):
        # Users should only see/modify their own appointments
        # TODO: Allow doctors to see/modify appointments they are part of
        return Appointment.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        """Override to trigger notification on status change."""
        old_instance = self.get_object()
        new_instance = serializer.save()

        if old_instance.status != new_instance.status and new_instance.status == 'confirmed':
            patient = new_instance.user
            doctor = new_instance.doctor
            # Assuming the update was likely done by the doctor or admin (need proper permission checks later)
            create_notification(
                recipient=patient,
                actor=doctor.user if hasattr(doctor, 'user') else None,
                verb=f"Your appointment with Dr. {doctor.last_name} on {new_instance.date.strftime('%b %d')} at {new_instance.start_time.strftime('%I:%M %p')} is confirmed.",
                level='appointment',
                target_url=f"/appointments/{new_instance.id}"
            )
            print(f"Confirmation notification created for user {patient.id} for appointment {new_instance.id}")
            
        elif old_instance.status != new_instance.status and new_instance.status == 'completed':

            new_prescription = Prescription.objects.filter(appointment=new_instance).first()
            if new_prescription:
                 patient = new_instance.user
                 create_notification(
                    recipient=patient,
                    actor=new_instance.doctor.user if hasattr(new_instance.doctor, 'user') else None,
                    verb=f"Your prescription from Dr. {new_instance.doctor.last_name} is ready.",
                    level='prescription',
                    target_url=f"/prescriptions/{new_prescription.id}"
                )
                 print(f"Prescription ready notification created for user {patient.id}")

        elif old_instance.status != new_instance.status and new_instance.status == 'cancelled':
            patient = new_instance.user
            doctor = new_instance.doctor
            other_party = None
            canceller = self.request.user
            if canceller == patient:
                other_party = doctor.user if hasattr(doctor, 'user') and doctor.user else None 
                cancelled_by = f"{patient.first_name} {patient.last_name}".strip() or patient.username
            elif hasattr(canceller, 'doctor_profile') and canceller.doctor_profile == doctor:
                other_party = patient
                cancelled_by = f"Dr. {doctor.last_name}"
            else:
                other_party = patient

            if other_party:
                 create_notification(
                    recipient=other_party,
                    actor=canceller,
                    verb=f"The appointment for {new_instance.date.strftime('%b %d')} at {new_instance.start_time.strftime('%I:%M %p')} with {'Dr. '+doctor.last_name if other_party == patient else patient.username} was cancelled by {cancelled_by}.",
                    level='warning', # Or 'info'
                    target_url=f"/appointments/{new_instance.id}"
                )
                 print(f"Cancellation notification created for user {other_party.id} for appointment {new_instance.id}")

class GetTwilioTokenView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, appointment_id, *args, **kwargs):
        try:
            appointment = get_object_or_404(Appointment, pk=appointment_id)
        except ValueError:
             return Response({"error": "Invalid Appointment ID format."}, status=status.HTTP_400_BAD_REQUEST)

        is_patient = (request.user == appointment.user)
        is_doctor = hasattr(request.user, 'doctor_profile') and (request.user.doctor_profile == appointment.doctor)

        if not (is_patient or is_doctor):
            return Response(
                {"error": "You do not have permission to join this video call."},
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment.appointment_type != 'virtual':
             return Response({"error": "This is not a virtual appointment."}, status=status.HTTP_400_BAD_REQUEST)

        if appointment.status not in ['confirmed', 'scheduled']:
             return Response({"error": f"Cannot join appointment with status '{appointment.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        account_sid = settings.TWILIO_ACCOUNT_SID
        api_key_sid = settings.TWILIO_API_KEY_SID
        api_key_secret = settings.TWILIO_API_KEY_SECRET

        if not all([account_sid, api_key_sid, api_key_secret]):
             print("ERROR: Twilio credentials missing in settings.")
             return Response({"error": "Video service configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        identity = f"{'patient' if is_patient else 'doctor'}_{request.user.id}"

        room_name = f"vitanips_appointment_{appointment.id}"

        access_token = AccessToken(account_sid, api_key_sid, api_key_secret, identity=identity, ttl=3600)

        video_grant = VideoGrant(room=room_name)
        access_token.add_grant(video_grant)

        jwt_token = access_token.to_jwt()

        print(f"Generated Twilio token for user '{identity}' for room '{room_name}'")

        return Response({'token': jwt_token, 'roomName': room_name, 'identity': identity})


class PrescriptionListView(generics.ListAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Prescription.objects.filter(user=self.request.user)
    
class PrescriptionDetailView(generics.RetrieveAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Prescription.objects.filter(user=self.request.user)