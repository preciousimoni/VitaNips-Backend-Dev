# doctors/views.py
import datetime
import logging
from django.conf import settings
from rest_framework import viewsets, generics, permissions, filters, views, status
from rest_framework import serializers
from django.urls import reverse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from notifications.utils import create_notification
from .permissions import IsDoctorUser, IsDoctorAssociatedWithAppointment, IsPrescribingDoctor
from .models import Specialty, Doctor, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem
from .serializers import (
    SpecialtySerializer, DoctorSerializer, DoctorReviewSerializer,
    DoctorAvailabilitySerializer, AppointmentSerializer, PrescriptionSerializer,
    DoctorPrescriptionCreateSerializer, DoctorPrescriptionListDetailSerializer,
    DoctorEligibleAppointmentSerializer, DoctorApplicationSerializer
)

logger = logging.getLogger(__name__)

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

class DoctorApplicationView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    """
    View for doctors to submit and manage their application.
    - POST: Submit new application
    - GET: Retrieve their application status
    - PATCH: Update application (only if status is 'draft' or 'needs_revision')
    """
    serializer_class = DoctorApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get the doctor profile for the authenticated user"""
        if hasattr(self.request.user, 'doctor_profile') and self.request.user.doctor_profile:
            return self.request.user.doctor_profile
        return None

    def get(self, request, *args, **kwargs):
        """Retrieve doctor's application"""
        doctor = self.get_object()
        if not doctor:
            return Response(
                {'error': 'No doctor profile found. Please submit an application first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Submit new application"""
        # Check if user already has a doctor profile
        if hasattr(request.user, 'doctor_profile') and request.user.doctor_profile:
            return Response(
                {'error': 'You already have a doctor profile. Use PATCH to update your application.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doctor = serializer.save()
        
        # Send notification to admins
        from notifications.utils import create_notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admins:
            create_notification(
                recipient=admin,
                actor=request.user,
                verb=f"New doctor application submitted by Dr. {doctor.first_name} {doctor.last_name}",
                title=f"New Doctor Application",
                level='info',
                category='system',
                action_url=f"/admin/doctors"
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        """Update application"""
        doctor = self.get_object()
        if not doctor:
            return Response(
                {'error': 'No doctor profile found. Please submit an application first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Allow updates if status is draft, needs_revision, or approved
        # If approved, we restrict certain fields below
        if doctor.application_status not in ['draft', 'needs_revision', 'approved']:
            return Response(
                {'error': f'Cannot update application. Current status: {doctor.get_application_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If approved, prevent changing critical fields that require verification
        if doctor.application_status == 'approved':
            restricted_fields = ['license_number', 'license_issuing_authority', 'license_expiry_date', 'specialty_ids']
            for field in restricted_fields:
                if field in request.data:
                    return Response(
                        {'error': f'Cannot update {field} after approval. Please contact support to update verified information.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        serializer = self.get_serializer(doctor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # If updating to submitted (from draft), set submitted_at
        if (serializer.validated_data.get('application_status') == 'submitted' or \
           (not serializer.validated_data.get('application_status') and doctor.application_status == 'draft')) and \
           doctor.application_status != 'approved':
            from django.utils import timezone
            doctor.submitted_at = timezone.now()
            doctor.application_status = 'submitted'
        
        serializer.save()
        
        # Notify admins if status changed to submitted
        if doctor.application_status == 'submitted':
            from notifications.utils import create_notification
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True, is_superuser=True)
            for admin in admins:
                create_notification(
                    recipient=admin,
                    actor=request.user,
                    verb=f"Doctor application updated and resubmitted by Dr. {doctor.first_name} {doctor.last_name}",
                    title=f"Doctor Application Updated",
                    level='info',
                    category='system',
                    action_url=f"/admin/doctors"
                )
        
        return Response(serializer.data)

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

class DoctorAvailabilityManageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for doctors to manage their own availability.
    Only allows doctors to view/edit their own availability.
    """
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def get_queryset(self):
        """Only return availability for the authenticated doctor"""
        if hasattr(self.request.user, 'doctor_profile') and self.request.user.doctor_profile:
            return DoctorAvailability.objects.filter(doctor=self.request.user.doctor_profile)
        return DoctorAvailability.objects.none()

    def perform_create(self, serializer):
        """Automatically set the doctor to the authenticated user's doctor profile"""
        if hasattr(self.request.user, 'doctor_profile') and self.request.user.doctor_profile:
            serializer.save(doctor=self.request.user.doctor_profile)
        else:
            raise permissions.PermissionDenied("You must be a doctor to manage availability.")

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If user is a doctor, show appointments where they are the doctor
        if hasattr(user, 'doctor_profile') and user.doctor_profile:
            return Appointment.objects.filter(doctor=user.doctor_profile)
        # Otherwise, show appointments where they are the patient
        return Appointment.objects.filter(user=user)

    def perform_create(self, serializer):
        # Check subscription limits before creating appointment
        from payments.utils import user_can_book_appointment
        from payments.models import UserSubscription
        
        if not user_can_book_appointment(self.request.user):
            subscription = UserSubscription.objects.filter(
                user=self.request.user,
                status='active'
            ).first()
            
            if subscription and subscription.is_active:
                max_appointments = subscription.plan.max_appointments_per_month
                limit_text = f"{max_appointments} appointments/month" if max_appointments else "unlimited"
                
                # Check monthly limit for premium
                from datetime import datetime
                from django.utils import timezone
                month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
                current_count = Appointment.objects.filter(
                    user=self.request.user,
                    created_at__gte=month_start,
                    status__in=['scheduled', 'confirmed', 'completed']
                ).count()
                limit_val = max_appointments
            else:
                from django.conf import settings
                free_limit = getattr(settings, 'FREEMIUM_APPOINTMENT_LIMIT', 3)
                limit_text = f"{free_limit} free lifetime appointments"
                # Check lifetime limit for free tier
                current_count = Appointment.objects.filter(
                    user=self.request.user,
                    status__in=['scheduled', 'confirmed', 'completed']
                ).count()
                limit_val = free_limit
            
            raise serializers.ValidationError({
                'error': 'Appointment limit reached',
                'message': f'You have reached your appointment limit ({limit_text}). Upgrade to Premium for unlimited appointments.',
                'current_count': current_count,
                'limit': limit_val,
                'upgrade_url': '/subscription'
            })

class DoctorBankDetailsView(views.APIView):
    """
    View for doctors to submit and view bank details.
    GET /api/doctors/portal/onboarding/bank/ - View existing bank details
    POST /api/doctors/portal/onboarding/bank/ - Submit/update bank details
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def get(self, request, *args, **kwargs):
        """Get existing bank details for the doctor."""
        doctor = request.user.doctor_profile
        
        if doctor.bank_account_details and doctor.subaccount_id:
            return Response({
                'has_bank_details': True,
                'bank_details': doctor.bank_account_details,
                'subaccount_id': doctor.subaccount_id,
                'commission_rate': float(doctor.commission_rate)
            })
        else:
            return Response({
                'has_bank_details': False,
                'message': 'No bank details found. Please add your bank account.'
            })

    def post(self, request, *args, **kwargs):
        doctor = request.user.doctor_profile
        
        # Validate input
        account_bank = request.data.get('account_bank') # Bank Code (e.g., '044')
        account_number = request.data.get('account_number')
        
        if not account_bank or not account_number:
            return Response(
                {'error': 'Bank code and account number are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify account name with Flutterwave
        from payments.utils import verify_bank_account
        
        verification_result = verify_bank_account(account_number, account_bank)
        
        if not verification_result or verification_result.get('status') != 'success':
            return Response(
                {'error': 'Failed to verify bank account. Please check your account number and bank.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        account_name = verification_result.get('data', {}).get('account_name', 'Unknown')
            
        # Create subaccount on Flutterwave
        from payments.utils import create_flutterwave_subaccount
        
        business_name = f"Dr. {doctor.first_name} {doctor.last_name}"
        business_email = doctor.user.email
        business_mobile = doctor.user.phone_number or "0000000000"
        
        response = create_flutterwave_subaccount(
            account_bank=account_bank,
            account_number=account_number,
            business_name=business_name,
            business_email=business_email,
            business_contact_mobile=business_mobile,
            business_mobile=business_mobile,
            split_value=float(1 - (doctor.commission_rate / 100)) # Doctor gets (100 - commission)%
        )
        
        if response and response.get('status') == 'success':
            data = response.get('data', {})
            doctor.subaccount_id = data.get('subaccount_id')
            doctor.bank_account_details = {
                'bank_code': account_bank,
                'account_number': account_number,
                'bank_name': data.get('bank_name', 'Unknown Bank'),
                'account_name': account_name
            }
            doctor.save()
            
            return Response({
                'message': 'Bank details updated and subaccount created successfully.',
                'subaccount_id': doctor.subaccount_id,
                'account_name': account_name,
                'bank_details': doctor.bank_account_details
            })
        else:
            return Response(
                {'error': 'Failed to create subaccount. Please check your bank details.', 'details': response},
                status=status.HTTP_400_BAD_REQUEST
            )

class DoctorVerifyBankAccountView(views.APIView):
    """
    Verify bank account details in real-time for doctors.
    POST /api/doctors/portal/verify-account/
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def post(self, request, *args, **kwargs):
        account_number = request.data.get('account_number')
        account_bank = request.data.get('account_bank')
        
        if not account_number or not account_bank:
            return Response(
                {'error': 'Account number and bank code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify account with Flutterwave
        from payments.utils import verify_bank_account
        
        result = verify_bank_account(account_number, account_bank)
        
        if result:
            return Response(result)
        else:
            return Response(
                {'status': 'error', 'message': 'Failed to verify account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        # Handle insurance if provided
        user_insurance_id = serializer.validated_data.pop('user_insurance_id', None)
        payment_reference = serializer.validated_data.pop('payment_reference', None)
        user_insurance = None
        
        if user_insurance_id:
            from insurance.models import UserInsurance
            try:
                user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=self.request.user)
            except UserInsurance.DoesNotExist:
                pass  # Continue without insurance if invalid
        
        # Check if payment is required
        doctor = serializer.validated_data.get('doctor')
        consultation_fee = None
        if doctor and doctor.consultation_fee:
            consultation_fee = doctor.consultation_fee
        
        # If no insurance and consultation fee exists, payment is required
        if not user_insurance and consultation_fee and consultation_fee > 0:
            # Allow creating appointment with payment_status='pending' without payment_reference
            # Payment reference will be added later via PATCH when payment is completed
            payment_status = 'paid' if payment_reference else 'pending'
            appointment = serializer.save(
                user=self.request.user,
                user_insurance=user_insurance,
                payment_reference=payment_reference if payment_reference else None,
                payment_status=payment_status,
                consultation_fee=consultation_fee
            )
        else:
            # With insurance or no fee - payment not required
            # Set payment_status based on whether payment_reference exists
            payment_status = 'paid' if payment_reference else 'pending'
            appointment = serializer.save(
                user=self.request.user,
                user_insurance=user_insurance,
                payment_reference=payment_reference if payment_reference else None,
                payment_status=payment_status,
                consultation_fee=consultation_fee if consultation_fee else None
            )
        
        # Calculate insurance coverage if insurance is selected
        if user_insurance and appointment.consultation_fee:
            from insurance.utils import calculate_insurance_coverage
            from decimal import Decimal
            
            consultation_fee = Decimal(str(appointment.consultation_fee))
            coverage = calculate_insurance_coverage(
                user_insurance,
                consultation_fee,
                service_type='consultation'
            )
            
            appointment.consultation_fee = consultation_fee
            appointment.insurance_covered_amount = coverage['covered_amount']
            appointment.patient_copay = coverage['patient_copay']
            appointment.save()

class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If user is a doctor, show appointments where they are the doctor
        if hasattr(user, 'doctor_profile') and user.doctor_profile:
            return Appointment.objects.filter(doctor=user.doctor_profile)
        # Otherwise, show appointments where they are the patient
        return Appointment.objects.filter(user=user)

    def perform_update(self, serializer):
        """Override to trigger notification on status change and handle insurance."""
        old_instance = self.get_object()
        
        # Handle insurance if being updated
        user_insurance_id = serializer.validated_data.pop('user_insurance_id', None)
        user_insurance = old_instance.user_insurance  # Keep existing if not updating
        
        if user_insurance_id is not None:  # Explicitly set (could be None to remove)
            from insurance.models import UserInsurance
            from insurance.utils import calculate_insurance_coverage
            from decimal import Decimal
            
            if user_insurance_id:
                try:
                    user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=self.request.user)
                except UserInsurance.DoesNotExist:
                    pass  # Keep existing insurance if invalid
            else:
                user_insurance = None  # Remove insurance
        
        # Handle payment_reference if provided (from payment callback)
        payment_reference = serializer.validated_data.pop('payment_reference', None)
        old_payment_status = old_instance.payment_status
        
        # Save the appointment first
        new_instance = serializer.save(user_insurance=user_insurance)
        
        # Update payment fields if payment_reference is provided
        payment_status_changed = False
        if payment_reference:
            new_instance.payment_reference = payment_reference
            new_instance.payment_status = 'paid'
            new_instance.save()
            payment_status_changed = (old_payment_status != 'paid' and new_instance.payment_status == 'paid')
        
        # Send notification when payment is confirmed
        if payment_status_changed:
            try:
                patient = new_instance.user
                doctor_name = new_instance.doctor.full_name if new_instance.doctor else "Doctor"
                create_notification(
                    recipient=patient,
                    verb=f"Payment confirmed for your appointment with {doctor_name} on {new_instance.date.strftime('%b %d')} at {new_instance.start_time.strftime('%I:%M %p')}.",
                    title=f"Payment Confirmed - Appointment",
                    level='success',
                    category='appointment',
                    action_url=f"/appointments/{new_instance.id}",
                    action_text="View Appointment"
                )
                print(f"Payment confirmation notification created for user {patient.id} for appointment {new_instance.id}")
            except Exception as e:
                print(f"Error creating payment confirmation notification for appointment {new_instance.id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Calculate insurance coverage if insurance is set (after saving, since these fields are read-only)
        if user_insurance:
            consultation_fee = new_instance.doctor.consultation_fee if new_instance.doctor and new_instance.doctor.consultation_fee else Decimal('0.00')
            
            if consultation_fee > 0:
                coverage = calculate_insurance_coverage(
                    user_insurance,
                    consultation_fee,
                    service_type='consultation'
                )
                # Set these fields directly on the instance since they're read-only in serializer
                new_instance.consultation_fee = consultation_fee
                new_instance.insurance_covered_amount = coverage['covered_amount']
                new_instance.patient_copay = coverage['patient_copay']
                new_instance.save()
        
        # Generate insurance claim automatically when appointment is completed
        if old_instance.status != new_instance.status and new_instance.status == 'completed':
            if new_instance.user_insurance and new_instance.consultation_fee and not new_instance.insurance_claim_generated:
                from insurance.utils import generate_insurance_claim
                from django.utils import timezone
                from decimal import Decimal
                
                try:
                    # Get doctor name (full_name already includes "Dr.")
                    doctor_name = new_instance.doctor.full_name if new_instance.doctor else "Unknown Doctor"
                    
                    # Ensure we have a valid date
                    service_date = new_instance.date
                    if not service_date:
                        service_date = timezone.now().date()
                    
                    # Ensure we have valid amounts
                    claimed_amount = new_instance.consultation_fee or Decimal('0.00')
                    approved_amount = new_instance.insurance_covered_amount or Decimal('0.00')
                    patient_responsibility = new_instance.patient_copay or Decimal('0.00')
                    
                    claim = generate_insurance_claim(
                        user_insurance=new_instance.user_insurance,
                        service_type='consultation',
                        service_date=service_date,
                        provider_name=doctor_name,
                        service_description=f"Consultation - {new_instance.reason or 'General consultation'}",
                        claimed_amount=claimed_amount,
                        approved_amount=approved_amount,
                        patient_responsibility=patient_responsibility,
                    )
                    new_instance.insurance_claim_generated = True
                    new_instance.save()
                except Exception as e:
                    import traceback
                    print(f"Error generating insurance claim for appointment {new_instance.id}: {e}")
                    print(traceback.format_exc())
                    # Don't fail the appointment update if claim generation fails

        # Send notifications for appointment status changes
        status_changed = old_instance.status != new_instance.status
        if status_changed:
            try:
                patient = new_instance.user
                doctor = new_instance.doctor
                if not doctor or not patient:
                    return
                
                doctor_name = doctor.full_name if doctor.full_name else (doctor.last_name if doctor.last_name else (doctor.first_name if doctor.first_name else "Doctor"))
                date_str = new_instance.date.strftime('%b %d') if new_instance.date else "TBD"
                time_str = new_instance.start_time.strftime('%I:%M %p') if new_instance.start_time else "TBD"
                
                if new_instance.status == 'scheduled':
                    create_notification(
                        recipient=patient,
                        verb=f"Your appointment with {doctor_name} has been scheduled for {date_str} at {time_str}.",
                        title=f"Appointment Scheduled",
                        level='info',
                        category='appointment',
                        action_url=f"/appointments/{new_instance.id}",
                        action_text="View Appointment"
                    )
                elif new_instance.status == 'confirmed':
                    create_notification(
                        recipient=patient,
                        verb=f"Your appointment with {doctor_name} on {date_str} at {time_str} is confirmed.",
                        title=f"Appointment Confirmed",
                        level='success',
                        category='appointment',
                        action_url=f"/appointments/{new_instance.id}",
                        action_text="View Appointment"
                    )
                elif new_instance.status == 'rescheduled':
                    create_notification(
                        recipient=patient,
                        verb=f"Your appointment with {doctor_name} has been rescheduled to {date_str} at {time_str}.",
                        title=f"Appointment Rescheduled",
                        level='info',
                        category='appointment',
                        action_url=f"/appointments/{new_instance.id}",
                        action_text="View Appointment"
                    )
                elif new_instance.status == 'completed':
                    new_prescription = Prescription.objects.filter(appointment=new_instance).first()
                    if new_prescription:
                        create_notification(
                            recipient=patient,
                            verb=f"Your appointment with {doctor_name} is completed. Your prescription is ready.",
                            title=f"Appointment Completed - Prescription Ready",
                            level='success',
                            category='prescription',
                            action_url=f"/prescriptions/{new_prescription.id}",
                            action_text="View Prescription"
                        )
                    else:
                        create_notification(
                            recipient=patient,
                            verb=f"Your appointment with {doctor_name} has been completed.",
                            title=f"Appointment Completed",
                            level='success',
                            category='appointment',
                            action_url=f"/appointments/{new_instance.id}",
                            action_text="View Appointment"
                        )
                elif new_instance.status == 'cancelled':
                    canceller = self.request.user
                    cancelled_by = f"{canceller.first_name} {canceller.last_name}".strip() if canceller != patient else "You"
                    
                    create_notification(
                        recipient=patient,
                        verb=f"Your appointment with {doctor_name} on {date_str} at {time_str} was cancelled by {cancelled_by}.",
                        title=f"Appointment Cancelled",
                        level='warning',
                        category='appointment',
                        action_url=f"/appointments/{new_instance.id}",
                        action_text="View Details"
                    )
                    
                    # Also notify doctor if patient cancelled
                    if canceller == patient and doctor and hasattr(doctor, 'user') and doctor.user:
                        create_notification(
                            recipient=doctor.user,
                            verb=f"Appointment with {patient.first_name} {patient.last_name} on {date_str} at {time_str} was cancelled by the patient.",
                            title=f"Appointment Cancelled",
                            level='warning',
                            category='appointment',
                            action_url=f"/appointments/{new_instance.id}",
                            action_text="View Details"
                        )
                
                print(f"Status change notification created for user {patient.id} for appointment {new_instance.id} (status: {new_instance.status})")
            except Exception as e:
                import traceback
                print(f"Error creating status change notification for appointment {new_instance.id}: {e}")
                print(traceback.format_exc())
                # Don't fail the appointment update if notification creation fails

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


class ForwardPrescriptionView(views.APIView):
    """
    Forward a prescription to a selected pharmacy by creating a medication order.
    POST /api/doctors/prescriptions/<pk>/forward/
    Body: {"pharmacy_id": <int>}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        # Import here to avoid circular imports
        from pharmacy.models import Pharmacy, MedicationOrder, MedicationOrderItem
        from django.db import transaction
        
        # Get the prescription
        try:
            prescription = Prescription.objects.select_related('appointment', 'user', 'doctor').get(
                pk=pk,
                user=request.user  # Ensure user owns this prescription
            )
        except Prescription.DoesNotExist:
            return Response(
                {"error": "Prescription not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get pharmacy_id from request
        pharmacy_id = request.data.get('pharmacy_id')
        if not pharmacy_id:
            return Response(
                {"error": "pharmacy_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate pharmacy exists and is active
        try:
            pharmacy = Pharmacy.objects.get(pk=pharmacy_id, is_active=True)
        except Pharmacy.DoesNotExist:
            return Response(
                {"error": "Pharmacy not found or is inactive."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if appointment is completed
        if prescription.appointment.status != 'completed':
            return Response(
                {"error": f"Cannot forward prescription. The appointment must be completed first. Current status: {prescription.appointment.get_status_display()}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if order already exists for this prescription
        existing_order = MedicationOrder.objects.filter(prescription=prescription).first()
        if existing_order:
            return Response(
                {
                    "error": "An order for this prescription already exists.",
                    "order_id": existing_order.id,
                    "pharmacy": existing_order.pharmacy.name,
                    "status": existing_order.status
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Check if prescription has items
        prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
        if not prescription_items.exists():
            return Response(
                {"error": "Prescription has no items to order."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the order
        try:
            with transaction.atomic():
                # Create medication order
                order = MedicationOrder.objects.create(
                    user=request.user,
                    pharmacy=pharmacy,
                    prescription=prescription,
                    status='pending',
                    notes=f"Order created from prescription #{prescription.id}"
                )
                
                # Create order items from prescription items
                order_items = []
                for p_item in prescription_items:
                    order_item = MedicationOrderItem(
                        order=order,
                        prescription_item=p_item,
                        medication_name_text=p_item.medication_name,
                        dosage_text=p_item.dosage,
                        quantity=1,  # Default quantity, pharmacy can adjust
                    )
                    order_items.append(order_item)
                
                MedicationOrderItem.objects.bulk_create(order_items)
                
                # Create notification for user
                create_notification(
                    recipient=request.user,
                    verb=f"Your prescription has been forwarded to {pharmacy.name}. Order #{order.id} is being processed.",
                    title=f"Prescription Forwarded - Order #{order.id}",
                    level='success',
                    category='order',
                    action_url=f"/orders/{order.id}",
                    action_text="View Order"
                )
                
                # Log the action
                logger.info(
                    f"Prescription {prescription.id} forwarded to pharmacy {pharmacy.id} "
                    f"by user {request.user.id}. Order {order.id} created."
                )
                
                # Return the created order details
                from pharmacy.serializers import MedicationOrderSerializer
                serializer = MedicationOrderSerializer(order)
                return Response(
                    {
                        "message": f"Prescription successfully forwarded to {pharmacy.name}.",
                        "order": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"Error forwarding prescription {pk}: {str(e)}")
            return Response(
                {"error": "An error occurred while creating the order. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
class DoctorEligibleAppointmentListView(generics.ListAPIView):
    serializer_class = DoctorEligibleAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def get_queryset(self):
        doctor_profile = self.request.user.doctor_profile
        return Appointment.objects.filter(
            doctor=doctor_profile,
            status=Appointment.StatusChoices.COMPLETED
        ).order_by('-date', '-start_time')


class DoctorPrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return DoctorPrescriptionCreateSerializer
        return DoctorPrescriptionListDetailSerializer

    def get_queryset(self):
        return Prescription.objects.filter(doctor=self.request.user.doctor_profile).order_by('-date_prescribed')

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated, IsDoctorUser, IsPrescribingDoctor]
        return super().get_permissions()

    def perform_create(self, serializer):
        # The serializer's create method already handles doctor and user
        # We just need to create the notification after saving
        prescription = serializer.save()
        appointment = prescription.appointment
        patient = appointment.user
        doctor_name = self.request.user.doctor_profile.full_name if self.request.user.doctor_profile.full_name else f"Dr. {self.request.user.doctor_profile.last_name}"
        date_str = appointment.date.strftime('%b %d') if appointment.date else "your appointment"
        
        create_notification(
            recipient=patient,
            actor=self.request.user,
            verb=f"{doctor_name} has issued a new prescription for your appointment on {date_str}.",
            title=f"New Prescription Available",
            level='success',
            category='prescription',
            action_url=f"/prescriptions/{prescription.id}",
            action_text="View Prescription"
        )
        print(f"New prescription notification created for user {patient.id} for prescription {prescription.id}")
