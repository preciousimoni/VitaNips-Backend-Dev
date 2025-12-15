# vitanips/core/admin_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from doctors.models import Doctor, Appointment
from pharmacy.models import Pharmacy, MedicationOrder
from users.serializers import UserSerializer
from doctors.serializers import DoctorSerializer
from pharmacy.serializers import PharmacySerializer

User = get_user_model()


class AdminStatsView(APIView):
    """
    Get overall platform statistics for admin dashboard
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Get date ranges
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        # User stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_this_month = User.objects.filter(
            created_at__gte=this_month_start
        ).count()
        
        # Doctor stats
        total_doctors = Doctor.objects.count()
        verified_doctors = Doctor.objects.filter(is_verified=True).count()
        pending_verification = Doctor.objects.filter(is_verified=False).count()
        
        # Pharmacy stats
        total_pharmacies = Pharmacy.objects.count()
        active_pharmacies = Pharmacy.objects.filter(is_active=True).count()
        
        # Appointment stats
        total_appointments = Appointment.objects.count()
        appointments_this_month = Appointment.objects.filter(
            date__gte=this_month_start
        ).count()
        appointments_today = Appointment.objects.filter(
            date=today
        ).count()
        
        # Order stats
        total_orders = MedicationOrder.objects.count()
        pending_orders = MedicationOrder.objects.filter(
            status='pending'
        ).count()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'new_this_month': new_users_this_month,
                'inactive': total_users - active_users,
            },
            'doctors': {
                'total': total_doctors,
                'verified': verified_doctors,
                'pending_verification': pending_verification,
            },
            'pharmacies': {
                'total': total_pharmacies,
                'active': active_pharmacies,
                'inactive': total_pharmacies - active_pharmacies,
            },
            'appointments': {
                'total': total_appointments,
                'this_month': appointments_this_month,
                'today': appointments_today,
            },
            'orders': {
                'total': total_orders,
                'pending': pending_orders,
            }
        }
        
        return Response(stats, status=status.HTTP_200_OK)


class AdminUsersListView(APIView):
    """
    List all users with filtering and pagination
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        
        # Filtering
        role = request.query_params.get('role', None)
        is_active = request.query_params.get('is_active', None)
        search = request.query_params.get('search', None)
        
        if role == 'admin':
            users = users.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif role == 'doctor':
            users = users.filter(doctor_profile__isnull=False)
        elif role == 'pharmacy':
            users = users.filter(is_pharmacy_staff=True)
        elif role == 'patient':
            users = users.filter(
                is_staff=False,
                is_pharmacy_staff=False,
                doctor_profile__isnull=True
            )
        
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        serializer = UserSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """
    Get, update, or delete a specific user
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Allow updating specific admin fields
            allowed_fields = ['is_active', 'is_staff', 'is_superuser', 'is_pharmacy_staff']
            for field in allowed_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            
            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminDoctorsListView(APIView):
    """
    List all doctors with verification status filtering
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        doctors = Doctor.objects.all().select_related('user').order_by('-created_at')
        
        # Filtering
        verification_status = request.query_params.get('verified', None)
        search = request.query_params.get('search', None)
        
        if verification_status is not None:
            doctors = doctors.filter(is_verified=verification_status.lower() == 'true')
        
        if search:
            doctors = doctors.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        serializer = DoctorSerializer(doctors, many=True)
        return Response({
            'count': doctors.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class AdminDoctorVerificationView(APIView):
    """
    Comprehensive doctor application review and verification.
    Supports: approve, reject, request revision, contact hospital
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, doctor_id):
        try:
            doctor = Doctor.objects.select_related('user', 'reviewed_by').get(id=doctor_id)
            action = request.data.get('action')  # 'approve', 'reject', 'request_revision'
            review_notes = request.data.get('review_notes', '')
            rejection_reason = request.data.get('rejection_reason', '')
            contact_hospital = request.data.get('contact_hospital', False)
            
            from notifications.utils import create_notification
            
            if action == 'approve':
                doctor.is_verified = True
                doctor.application_status = 'approved'
                doctor.reviewed_at = timezone.now()
                doctor.reviewed_by = request.user
                doctor.review_notes = review_notes
                doctor.rejection_reason = None
                doctor.save()
                
                # Notify doctor
                if doctor.user:
                    create_notification(
                        recipient=doctor.user,
                        actor=request.user,
                        verb=f"Your doctor application has been approved! You can now start accepting appointments.",
                        level='success',
                        target_url=f"/doctor/dashboard"
                    )
                
                return Response({
                    'message': 'Doctor application approved successfully',
                    'doctor': DoctorSerializer(doctor).data
                }, status=status.HTTP_200_OK)
            
            elif action == 'reject':
                if not rejection_reason:
                    return Response(
                        {'error': 'rejection_reason is required when rejecting an application'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                doctor.is_verified = False
                doctor.application_status = 'rejected'
                doctor.reviewed_at = timezone.now()
                doctor.reviewed_by = request.user
                doctor.review_notes = review_notes
                doctor.rejection_reason = rejection_reason
                doctor.save()
                
                # Notify doctor
                if doctor.user:
                    create_notification(
                        recipient=doctor.user,
                        actor=request.user,
                        verb=f"Your doctor application has been rejected. Reason: {rejection_reason}",
                        level='error',
                        target_url=f"/doctor/application"
                    )
                
                return Response({
                    'message': 'Doctor application rejected',
                    'doctor': DoctorSerializer(doctor).data
                }, status=status.HTTP_200_OK)
            
            elif action == 'request_revision':
                doctor.application_status = 'needs_revision'
                doctor.reviewed_at = timezone.now()
                doctor.reviewed_by = request.user
                doctor.review_notes = review_notes
                doctor.rejection_reason = None
                doctor.save()
                
                # Notify doctor
                if doctor.user:
                    create_notification(
                        recipient=doctor.user,
                        actor=request.user,
                        verb=f"Your doctor application needs revision. Please review the admin notes and resubmit.",
                        level='warning',
                        target_url=f"/doctor/application"
                    )
                
                return Response({
                    'message': 'Revision requested from doctor',
                    'doctor': DoctorSerializer(doctor).data
                }, status=status.HTTP_200_OK)
            
            elif action == 'start_review':
                doctor.application_status = 'under_review'
                doctor.reviewed_by = request.user
                doctor.save()
                
                return Response({
                    'message': 'Review started',
                    'doctor': DoctorSerializer(doctor).data
                }, status=status.HTTP_200_OK)
            
            elif action == 'contact_hospital':
                # This would typically trigger an email/SMS to the hospital
                # For now, we'll just log it and return success
                hospital_info = {
                    'name': doctor.hospital_name,
                    'phone': doctor.hospital_phone,
                    'email': doctor.hospital_email,
                    'contact_person': doctor.hospital_contact_person,
                }
                
                # Add note about hospital contact
                contact_note = f"\n[Hospital Contacted on {timezone.now().strftime('%Y-%m-%d %H:%M')}]"
                doctor.review_notes = (doctor.review_notes or '') + contact_note
                doctor.save()
                
                return Response({
                    'message': 'Hospital contact information retrieved',
                    'hospital_info': hospital_info,
                    'note': 'In production, this would send an email/SMS to the hospital for verification'
                }, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {'error': f'Invalid action. Must be one of: approve, reject, request_revision, start_review, contact_hospital'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminPharmaciesListView(APIView):
    """
    List all pharmacies
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        pharmacies = Pharmacy.objects.all().order_by('-created_at')
        
        # Filtering
        is_active = request.query_params.get('is_active', None)
        search = request.query_params.get('search', None)
        
        if is_active is not None:
            pharmacies = pharmacies.filter(is_active=is_active.lower() == 'true')
        
        if search:
            pharmacies = pharmacies.filter(
                Q(name__icontains=search) |
                Q(address__icontains=search) |
                Q(email__icontains=search)
            )
        
        serializer = PharmacySerializer(pharmacies, many=True)
        return Response({
            'count': pharmacies.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class AdminPharmacyDetailView(APIView):
    """
    Update pharmacy status
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pharmacy_id):
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            
            if 'is_active' in request.data:
                pharmacy.is_active = request.data['is_active']
                pharmacy.save()
            
            serializer = PharmacySerializer(pharmacy)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Pharmacy.DoesNotExist:
            return Response(
                {'error': 'Pharmacy not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminAnalyticsView(APIView):
    """
    Get detailed analytics data for charts and reports
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from calendar import monthrange
        
        today = timezone.now().date()
        
        # User growth over last 12 months (more accurate calculation)
        user_growth = []
        for i in range(11, -1, -1):  # Last 12 months including current
            # Calculate month start by going back i months
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            
            month_start = today.replace(year=year, month=month, day=1)
            
            # Calculate last day of month properly
            last_day = monthrange(month_start.year, month_start.month)[1]
            month_end = month_start.replace(day=last_day) + timedelta(days=1)
            
            count = User.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            user_growth.append({
                'month': month_start.strftime('%b %Y'),
                'count': count
            })
        
        # Appointments by status (handle TextChoices properly)
        appointment_stats = []
        status_counts = Appointment.objects.values('status').annotate(
            count=Count('id')
        )
        for stat in status_counts:
            appointment_stats.append({
                'status': stat['status'],
                'count': stat['count']
            })
        
        # Top specialties (handle ManyToMany properly)
        top_specialties = Doctor.objects.values(
            'specialties__name'
        ).annotate(
            count=Count('id', distinct=True)
        ).filter(specialties__name__isnull=False).order_by('-count')[:10]
        
        specialties_list = []
        for spec in top_specialties:
            specialties_list.append({
                'specialties__name': spec['specialties__name'] or 'General',
                'count': spec['count']
            })
        
        analytics = {
            'user_growth': user_growth,
            'appointments_by_status': appointment_stats,
            'top_specialties': specialties_list,
        }
        
        return Response(analytics, status=status.HTTP_200_OK)


class AdminAppointmentsListView(APIView):
    """
    List all appointments on the platform (admin only)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from doctors.serializers import AppointmentSerializer
        
        # Get query parameters
        status_filter = request.query_params.get('status', None)
        search_query = request.query_params.get('search', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        # Start with all appointments
        appointments = Appointment.objects.select_related(
            'user', 'doctor', 'doctor__user'
        ).order_by('-date', '-start_time')
        
        # Apply filters
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        if date_from:
            appointments = appointments.filter(date__gte=date_from)
        
        if date_to:
            appointments = appointments.filter(date__lte=date_to)
        
        if search_query:
            appointments = appointments.filter(
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(doctor__first_name__icontains=search_query) |
                Q(doctor__last_name__icontains=search_query) |
                Q(reason__icontains=search_query)
            )
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = appointments.count()
        appointments_page = appointments[start:end]
        
        serializer = AppointmentSerializer(appointments_page, many=True, context={'request': request})
        
        return Response({
            'count': total_count,
            'next': f'/admin/appointments/?page={page + 1}' if end < total_count else None,
            'previous': f'/admin/appointments/?page={page - 1}' if page > 1 else None,
            'results': serializer.data
        }, status=status.HTTP_200_OK)



class AdminAppointmentDetailView(APIView):
    """
    Get a specific appointment details
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, appointment_id):
        from doctors.serializers import AppointmentSerializer
        try:
            appointment = Appointment.objects.select_related(
                'user', 'doctor', 'doctor__user'
            ).get(id=appointment_id)
            serializer = AppointmentSerializer(appointment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminRecentActivityView(APIView):
    """
    Get recent admin activities for the dashboard
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from datetime import timedelta
        
        # Get activities from last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        activities = []
        
        # 1. Recent doctor verifications
        recent_doctor_verifications = Doctor.objects.filter(
            reviewed_at__gte=seven_days_ago,
            reviewed_by__isnull=False
        ).select_related('user', 'reviewed_by').order_by('-reviewed_at')[:10]
        
        for doctor in recent_doctor_verifications:
            if doctor.is_verified:
                action = 'approved'
                icon = 'check-circle'
                color = 'green'
            elif doctor.application_status == 'rejected':
                action = 'rejected'
                icon = 'x-circle'
                color = 'red'
            else:
                action = 'reviewed'
                icon = 'clock'
                color = 'blue'
            
            activities.append({
                'id': f'doctor_{doctor.id}_{doctor.reviewed_at.timestamp()}',
                'type': 'doctor_verification',
                'action': action,
                'description': f"{action.capitalize()} doctor application for Dr. {doctor.first_name} {doctor.last_name}",
                'target_name': f"Dr. {doctor.first_name} {doctor.last_name}",
                'actor_name': doctor.reviewed_by.get_full_name() or doctor.reviewed_by.username,
                'timestamp': doctor.reviewed_at.isoformat(),
                'icon': icon,
                'color': color,
            })
        
        # 2. Recent user creations (by admins or new registrations)
        recent_users = User.objects.filter(
            created_at__gte=seven_days_ago
        ).order_by('-created_at')[:10]
        
        for user in recent_users:
            user_type = 'patient'
            if user.is_staff or user.is_superuser:
                user_type = 'admin'
            elif hasattr(user, 'doctor_profile'):
                user_type = 'doctor'
            elif user.is_pharmacy_staff:
                user_type = 'pharmacy'
            
            activities.append({
                'id': f'user_{user.id}_{user.created_at.timestamp()}',
                'type': 'user_created',
                'action': 'created',
                'description': f"New {user_type} account created: {user.get_full_name() or user.username}",
                'target_name': user.get_full_name() or user.username,
                'actor_name': 'System',
                'timestamp': user.created_at.isoformat(),
                'icon': 'user-plus',
                'color': 'blue',
            })
        
        # 3. Recent user status changes (if we track this via updated_at and is_active changes)
        # This is a simplified version - in production you'd want an audit log
        recent_user_updates = User.objects.filter(
            updated_at__gte=seven_days_ago
        ).exclude(created_at__gte=seven_days_ago).order_by('-updated_at')[:5]
        
        for user in recent_user_updates:
            if not user.is_active:
                activities.append({
                    'id': f'user_deactivated_{user.id}_{user.updated_at.timestamp()}',
                    'type': 'user_status',
                    'action': 'deactivated',
                    'description': f"User account deactivated: {user.get_full_name() or user.username}",
                    'target_name': user.get_full_name() or user.username,
                    'actor_name': 'Admin',
                    'timestamp': user.updated_at.isoformat(),
                    'icon': 'user-minus',
                    'color': 'orange',
                })
        
        # 4. Recent appointments (significant ones)
        recent_completed_appointments = Appointment.objects.filter(
            status='completed',
            updated_at__gte=seven_days_ago
        ).select_related('user', 'doctor').order_by('-updated_at')[:5]
        
        for appointment in recent_completed_appointments:
            activities.append({
                'id': f'appointment_{appointment.id}_{appointment.updated_at.timestamp()}',
                'type': 'appointment',
                'action': 'completed',
                'description': f"Appointment completed: {appointment.patient_name or 'Patient'} with Dr. {appointment.doctor_name or 'Doctor'}",
                'target_name': appointment.patient_name or 'Patient',
                'actor_name': f"Dr. {appointment.doctor_name or 'Doctor'}",
                'timestamp': appointment.updated_at.isoformat(),
                'icon': 'check-circle',
                'color': 'green',
            })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return top 10 most recent
        return Response({
            'activities': activities[:10]
        }, status=status.HTTP_200_OK)
