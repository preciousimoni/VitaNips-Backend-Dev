from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from doctors.models import Doctor, Specialty
from pharmacy.models import Pharmacy
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with default users for testing (Patient, Doctor, Pharmacy Staff)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding users...')

        # 1. Create Pharmacy (needed for Pharmacy Staff)
        pharmacy, _ = Pharmacy.objects.get_or_create(
            name="VitaCare Pharmacy",
            defaults={
                'address': "123 Health St, Wellness City",
                'phone_number': "555-0123",
                'email': "contact@vitacare.com",
                'operating_hours': "9:00 AM - 9:00 PM",
                'is_active': True,
                'offers_delivery': True
            }
        )
        self.stdout.write(f"Ensured Pharmacy: {pharmacy.name}")

        # Helper to create or get user
        def create_test_user(email, username, password, **kwargs):
            try:
                user = User.objects.get(Q(email=email) | Q(username=username))
                self.stdout.write(self.style.WARNING(f"User {email}/{username} already exists. Updating password."))
                user.set_password(password)
                for key, value in kwargs.items():
                    setattr(user, key, value)
                user.save()
                return user, False
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    **kwargs
                )
                self.stdout.write(self.style.SUCCESS(f"Created User: {email} / {password}"))
                return user, True

        # 2. Create Patient User
        patient, created = create_test_user(
            'patient@example.com', 'patient', 'patientpassword',
            first_name='John', last_name='Doe', phone_number='+15550000001'
        )

        # 3. Create Doctor User & Profile
        doctor_user, created = create_test_user(
            'doctor@example.com', 'doctor', 'doctorpassword',
            first_name='Jane', last_name='Smith', phone_number='+15550000002'
        )
        
        specialty, _ = Specialty.objects.get_or_create(name="General Practice")
        
        doctor_profile, _ = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'gender': 'F',
                'years_of_experience': 10,
                'education': "MD, University of Medicine",
                'bio': "Experienced general practitioner focused on preventative care.",
                'languages_spoken': "English, Spanish",
                'is_verified': True
            }
        )
        if created:
             doctor_profile.specialties.add(specialty)
        
        # 4. Create Pharmacy Staff User
        staff_user, created = create_test_user(
            'pharmacist@example.com', 'pharmacist', 'pharmacistpassword',
            first_name='Bob', last_name='Pills', phone_number='+15550000003',
            is_pharmacy_staff=True, works_at_pharmacy=pharmacy
        )

        # 5. Ensure Admin (Superuser)
        try:
            admin = User.objects.get(Q(email='admin@example.com') | Q(username='admin'))
            self.stdout.write(self.style.WARNING(f"Admin admin@example.com already exists."))
            if not admin.is_superuser:
                admin.is_superuser = True
                admin.is_staff = True
                admin.save()
                self.stdout.write(self.style.SUCCESS(f"Promoted existing admin user to superuser."))
        except User.DoesNotExist:
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            self.stdout.write(self.style.SUCCESS(f"Created Admin: admin@example.com / adminpassword"))

        self.stdout.write(self.style.SUCCESS('User seeding completed successfully.'))
