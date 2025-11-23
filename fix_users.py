import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.contrib.auth import get_user_model
from pharmacy.models import Pharmacy

User = get_user_model()

def update_users():
    # 1. Patient
    try:
        patient = User.objects.get(username='patient')
        patient.email = 'patient@example.com'
        patient.set_password('patientpassword')
        patient.save()
        print("Updated Patient: patient@example.com / patientpassword")
    except User.DoesNotExist:
        patient = User.objects.create_user(username='patient', email='patient@example.com', password='patientpassword')
        print("Created Patient: patient@example.com / patientpassword")

    # 2. Doctor
    try:
        doctor = User.objects.get(username='doctor')
        doctor.email = 'doctor@example.com'
        doctor.set_password('doctorpassword')
        doctor.save()
        print("Updated Doctor: doctor@example.com / doctorpassword")
    except User.DoesNotExist:
        doctor = User.objects.create_user(username='doctor', email='doctor@example.com', password='doctorpassword', is_doctor=True)
        print("Created Doctor: doctor@example.com / doctorpassword")

    # 3. Pharmacist
    try:
        pharmacist = User.objects.get(username='pharmacist')
        pharmacist.email = 'pharmacist@example.com'
        pharmacist.set_password('pharmacistpassword')
        pharmacist.save()
        print("Updated Pharmacist: pharmacist@example.com / pharmacistpassword")
    except User.DoesNotExist:
        # Need a pharmacy for pharmacist
        pharmacy, _ = Pharmacy.objects.get_or_create(name="VitaCare Pharmacy", defaults={'address': '123 Main St'})
        pharmacist = User.objects.create_user(username='pharmacist', email='pharmacist@example.com', password='pharmacistpassword', is_pharmacy_staff=True, works_at_pharmacy=pharmacy)
        print("Created Pharmacist: pharmacist@example.com / pharmacistpassword")

    # 4. Admin
    try:
        admin = User.objects.get(username='admin')
        admin.email = 'admin@example.com'
        admin.set_password('adminpassword')
        admin.save()
        print("Updated Admin: admin@example.com / adminpassword")
    except User.DoesNotExist:
        admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpassword')
        print("Created Admin: admin@example.com / adminpassword")

if __name__ == '__main__':
    update_users()
