# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from .models import User, MedicalHistory, Vaccination
from insurance.serializers import UserInsuranceSerializer
from emergency.serializers import EmergencyContactSerializer
from vitanips.core.utils import send_app_email
from .tasks import send_welcome_email
# from doctors.serializers import DoctorProfileSummarySerializer

User = get_user_model()


class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = ['id', 'vaccine_name', 'date_administered', 'dose_number', 'next_dose_date', 
                 'administered_at', 'batch_number', 'user', 'notes']
        read_only_fields = ['id', 'user']


class UserSerializer(serializers.ModelSerializer):
    insurance_details = UserInsuranceSerializer(
        many=True, read_only=True, source='insurance_plans')
    emergency_contacts = EmergencyContactSerializer(
        many=True, read_only=True)
    vaccinations = VaccinationSerializer(
        many=True, read_only=True)

    is_doctor = serializers.SerializerMethodField()
    doctor_id = serializers.SerializerMethodField()
    # doctor_profile_summary = DoctorProfileSummarySerializer(source='doctor_profile', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'date_of_birth', 'profile_picture',
            'medical_history_summary',
            'blood_group', 'genotype', 'allergies',
            'chronic_conditions', 'weight', 'height',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push', 'is_pharmacy_staff', 'works_at_pharmacy',
            'insurance_details', 'emergency_contacts', 'vaccinations',
            'is_doctor', 'doctor_id', 'is_staff', 'is_superuser', 'is_active', 'created_at', 'updated_at',
            'registered_as_doctor',
            # 'doctor_profile_summary',
        ]
        read_only_fields = ['id', 'username', 'email',
                            'insurance_details', 'emergency_contacts', 'vaccinations',
                            'is_doctor', 'doctor_id', 'created_at',
                            'updated_at', 'is_pharmacy_staff', 'works_at_pharmacy',]

    def get_is_doctor(self, obj):
        # Check if the related 'doctor_profile' exists for the user object 'obj'
        try:
            return obj.doctor_profile is not None
        except AttributeError:  # More specific: User.doctor_profile.RelatedObjectDoesNotExist
            return False

    def get_doctor_id(self, obj):
        try:
            if obj.doctor_profile:
                return obj.doctor_profile.id
            return None
        except AttributeError:
            return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    is_doctor = serializers.BooleanField(write_only=True, required=False, default=False, help_text="Indicates if the user is registering as a doctor.")

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name',
                  'phone_number', 'date_of_birth', 'blood_group', 'genotype', 'allergies', 'is_doctor']
        extra_kwargs = {
            'password': {'write_only': True},
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
            'blood_group': {'required': False},
            'genotype': {'required': False},
            'allergies': {'required': False},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        is_doctor = validated_data.pop('is_doctor', False)
        user = User(**validated_data)
        user.set_password(password)
        # Store the doctor registration intent
        user.registered_as_doctor = is_doctor
        user.save()
        
        # Send welcome email - try Celery first, fallback to synchronous if Celery unavailable
        try:
            import logging
            from django.conf import settings
            logger = logging.getLogger(__name__)
            
            # Check if Celery broker is configured
            broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
            
            if broker_url:
                try:
                    logger.info(f"Queueing welcome email via Celery for user {user.id} ({user.email})")
                    send_welcome_email.delay(user.id)
                    logger.info(f"Welcome email task queued successfully for {user.email}")
                except Exception as celery_error:
                    logger.warning(f"Celery task failed, sending email synchronously: {celery_error}")
                    # Fallback to synchronous sending
                    send_welcome_email(user.id)
            else:
                # No Celery broker configured, send synchronously
                logger.info(f"Sending welcome email synchronously (no Celery broker) for {user.email}")
                send_welcome_email(user.id)
                
        except Exception as e:
            # Log error but don't fail registration if email fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send welcome email for {user.email}: {e}", exc_info=True)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'address', 'date_of_birth',
            'profile_picture', 'medical_history_summary',
            'blood_group', 'genotype', 'allergies',
            'chronic_conditions',
            'notify_appointment_confirmation_email', 'notify_appointment_cancellation_email',
            'notify_appointment_reminder_email', 'notify_prescription_update_email',
            'notify_order_update_email', 'notify_general_updates_email',
            'notify_refill_reminder_email', 'notify_appointment_reminder_sms',
            'notify_appointment_reminder_push',
            'weight', 'height',
        ]

        extra_kwargs = {
            'profile_picture': {'required': False, 'allow_null': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False, 'allow_null': True},
            'allergies': {'required': False},
            'chronic_conditions': {'required': False}
        }


class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


# Custom Password Reset Serializer to use frontend URL
class CustomPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        from django.contrib.auth.forms import PasswordResetForm
        from django.conf import settings
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        request = self.context.get('request')
        email = self.validated_data['email']
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Prepare email context
        context = {
            'user': user,
            'uid': uid,
            'token': token,
            'frontend_url': frontend_url,
            'protocol': 'https' if (request and request.is_secure()) else 'http',
        }
        
        # Render email templates
        subject = render_to_string('registration/password_reset_subject.txt', context)
        subject = ''.join(subject.splitlines())  # Remove newlines
        message_html = render_to_string('registration/password_reset_email.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message='',  # Empty plain text message since we're using HTML
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL'),
            recipient_list=[email],
            html_message=message_html,
            fail_silently=False,
        )
