# doctors/video_views.py
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from .models import Appointment, VirtualSession
import logging

logger = logging.getLogger(__name__)

class GenerateVideoTokenView(views.APIView):
    """
    Generate Twilio Video Access Token for authenticated users
    POST /api/doctors/appointments/{appointment_id}/video/token/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        # Fetch the appointment
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        
        # Authorization: User must be the patient or the doctor
        user = request.user
        is_patient = appointment.user == user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        
        if not (is_patient or is_doctor):
            return Response(
                {"error": "You do not have permission to join this consultation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if appointment is confirmed or scheduled
        if appointment.status not in [Appointment.StatusChoices.CONFIRMED, Appointment.StatusChoices.SCHEDULED]:
            return Response(
                {
                    "error": f"Video consultation is only available for confirmed appointments. Current status: {appointment.get_status_display()}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create VirtualSession
        virtual_session, created = VirtualSession.objects.get_or_create(
            appointment=appointment,
            defaults={'status': 'scheduled'}
        )
        
        # If this is the first time accessing, mark as active
        if virtual_session.status == 'scheduled':
            virtual_session.status = 'active'
            if not virtual_session.started_at:
                from django.utils import timezone
                virtual_session.started_at = timezone.now()
            virtual_session.save()
        
        # Generate Twilio Access Token
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            api_key_sid = settings.TWILIO_API_KEY_SID
            api_key_secret = settings.TWILIO_API_KEY_SECRET
            
            if not all([account_sid, api_key_sid, api_key_secret]):
                logger.error("Twilio credentials not properly configured")
                return Response(
                    {"error": "Video service is not configured. Please contact support."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create identity for the user
            identity = f"user-{user.id}"
            if is_doctor:
                identity = f"doctor-{user.doctor_profile.id}"
            
            # Create access token
            token = AccessToken(
                account_sid,
                api_key_sid,
                api_key_secret,
                identity=identity
            )
            
            # Create video grant
            video_grant = VideoGrant(room=virtual_session.room_name)
            token.add_grant(video_grant)
            
            # Generate the token
            jwt_token = token.to_jwt()
            
            logger.info(
                f"Generated video token for user {user.id} (identity: {identity}) "
                f"for appointment {appointment_id}, room: {virtual_session.room_name}"
            )
            
            return Response({
                "token": jwt_token,
                "room_name": virtual_session.room_name,
                "identity": identity,
                "session_status": virtual_session.status,
                "appointment": {
                    "id": appointment.id,
                    "doctor_name": appointment.doctor.full_name if appointment.doctor else "N/A",
                    "patient_name": f"{appointment.user.first_name} {appointment.user.last_name}",
                    "date": str(appointment.date),
                    "time": str(appointment.start_time),
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating Twilio token for appointment {appointment_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to generate video token. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EndVideoSessionView(views.APIView):
    """
    Mark a video session as completed
    POST /api/doctors/appointments/{appointment_id}/video/end/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        
        # Authorization
        user = request.user
        is_patient = appointment.user == user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        
        if not (is_patient or is_doctor):
            return Response(
                {"error": "You do not have permission to end this session."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            virtual_session = VirtualSession.objects.get(appointment=appointment)
            
            if virtual_session.status != 'completed':
                from django.utils import timezone
                virtual_session.status = 'completed'
                virtual_session.ended_at = timezone.now()
                
                # Calculate duration if started_at exists
                if virtual_session.started_at:
                    duration = virtual_session.ended_at - virtual_session.started_at
                    virtual_session.duration_minutes = int(duration.total_seconds() / 60)
                
                virtual_session.save()
                
                logger.info(f"Video session {virtual_session.id} ended by user {user.id}")
            
            return Response({
                "message": "Video session ended successfully.",
                "session": {
                    "id": virtual_session.id,
                    "status": virtual_session.status,
                    "duration_minutes": virtual_session.duration_minutes,
                }
            }, status=status.HTTP_200_OK)
            
        except VirtualSession.DoesNotExist:
            return Response(
                {"error": "No active video session found for this appointment."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error ending video session for appointment {appointment_id}: {str(e)}")
            return Response(
                {"error": "Failed to end video session."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
