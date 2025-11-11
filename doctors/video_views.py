# doctors/video_views.py
from rest_framework import views, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
from .models import Appointment, VirtualSession
from .serializers import VirtualSessionSerializer
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


# ========== ENHANCED ENDPOINTS ==========

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_virtual_session_enhanced(request, appointment_id):
    """
    Enhanced session start with Twilio Room creation
    
    POST /api/appointments/{id}/start_virtual_enhanced/
    """
    try:
        appointment = get_object_or_404(
            Appointment.objects.select_related('patient', 'doctor__user'),
            id=appointment_id
        )
        
        # Verify user is participant
        user = request.user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        is_patient = appointment.patient == user
        
        if not (is_doctor or is_patient):
            return Response(
                {'error': 'You are not authorized to join this appointment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check appointment status
        if appointment.status not in ['confirmed', 'scheduled', 'in_progress']:
            return Response(
                {'error': 'Appointment must be confirmed to start virtual session'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create virtual session
        virtual_session, created = VirtualSession.objects.get_or_create(
            appointment=appointment,
            defaults={'status': 'scheduled'}
        )
        
        # Create Twilio Room if not exists
        if not virtual_session.room_sid:
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                # Create a unique room name
                room_name = f"vitanips_appointment_{appointment.id}_{int(timezone.now().timestamp())}"
                
                # Create room with recording enabled
                room = client.video.v1.rooms.create(
                    unique_name=room_name,
                    type='group',
                    record_participants_on_connect=True,
                    max_participants=10
                )
                
                virtual_session.room_name = room.unique_name
                virtual_session.room_sid = room.sid
                virtual_session.status = 'active'
                virtual_session.started_at = timezone.now()
                virtual_session.save()
                
                # Update appointment status
                appointment.status = 'in_progress'
                appointment.save()
                
                logger.info(f"Created Twilio room {room.sid} for appointment {appointment_id}")
                
            except Exception as e:
                logger.error(f"Failed to create Twilio room: {e}")
                return Response(
                    {'error': 'Failed to create video room', 'detail': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Generate access token
        identity = f"{user.id}_{user.email}"
        token = generate_twilio_token(identity, virtual_session.room_name)
        
        try:
            serializer = VirtualSessionSerializer(virtual_session)
            session_data = serializer.data
        except:
            # Fallback if serializer not available
            session_data = {
                'id': virtual_session.id,
                'room_name': virtual_session.room_name,
                'room_sid': virtual_session.room_sid,
                'status': virtual_session.status,
            }
        
        return Response({
            'session': session_data,
            'token': token,
            'room_name': virtual_session.room_name,
            'room_sid': virtual_session.room_sid,
            'participant_role': 'doctor' if is_doctor else 'patient'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error starting virtual session: {e}")
        return Response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_session_recordings(request, appointment_id):
    """
    Get recordings for a completed virtual session
    
    GET /api/appointments/{id}/recordings/
    """
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Verify user is participant
        user = request.user
        is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
        is_patient = appointment.patient == user
        
        if not (is_doctor or is_patient):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        virtual_session = VirtualSession.objects.filter(appointment=appointment).first()
        
        if not virtual_session or not virtual_session.room_sid:
            return Response({'recordings': []}, status=status.HTTP_200_OK)
        
        # Fetch recordings from Twilio
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            recordings = client.video.v1.recordings.list(room_sid=virtual_session.room_sid)
            
            recording_data = []
            for recording in recordings:
                recording_data.append({
                    'sid': recording.sid,
                    'status': recording.status,
                    'duration': recording.duration,
                    'date_created': recording.date_created.isoformat() if recording.date_created else None,
                    'media_url': f"https://video.twilio.com/v1/Recordings/{recording.sid}/Media",
                    'size': recording.size,
                })
            
            return Response({'recordings': recording_data}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to fetch recordings: {e}")
            return Response(
                {'error': 'Failed to fetch recordings', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Error getting recordings: {e}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def twilio_webhook_room_status(request):
    """
    Webhook to receive Twilio room status updates
    
    POST /api/video/webhook/room-status/
    """
    try:
        room_sid = request.data.get('RoomSid')
        room_status = request.data.get('RoomStatus')
        
        logger.info(f"Twilio webhook - Room {room_sid} status: {room_status}")
        
        # Find and update virtual session
        virtual_session = VirtualSession.objects.filter(room_sid=room_sid).first()
        if virtual_session:
            if room_status == 'completed':
                virtual_session.status = 'completed'
                virtual_session.ended_at = timezone.now()
                if virtual_session.started_at:
                    duration = (virtual_session.ended_at - virtual_session.started_at).total_seconds() / 60
                    virtual_session.duration_minutes = int(duration)
                virtual_session.save()
        
        return Response({'status': 'received'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_twilio_token(user_identity, room_name, ttl=3600):
    """
    Generate Twilio Video Access Token
    
    Args:
        user_identity: Unique identifier for the user
        room_name: Name of the video room
        ttl: Token time-to-live in seconds (default 1 hour)
    
    Returns:
        JWT token string
    """
    token = AccessToken(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_API_KEY_SID,
        settings.TWILIO_API_KEY_SECRET,
        identity=user_identity,
        ttl=ttl
    )
    
    video_grant = VideoGrant(room=room_name)
    token.add_grant(video_grant)
    
    return token.to_jwt()
