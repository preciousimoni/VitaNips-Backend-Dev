from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import random
from faker import Faker

# === Import all models ===
from doctors.models import (
    Doctor, Specialty, DoctorReview, DoctorAvailability,
    Appointment, Prescription, PrescriptionItem
)
from pharmacy.models import (
    Pharmacy, Medication, PharmacyInventory,
    MedicationOrder, MedicationOrderItem, MedicationReminder
)
from health.models import (
    VitalSign, SymptomLog, FoodLog, ExerciseLog,
    SleepLog, HealthGoal, MedicalDocument
)
from insurance.models import (
    InsuranceProvider, InsurancePlan, UserInsurance,
    InsuranceClaim, InsuranceDocument
)

fake = Faker()
User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with comprehensive mock data for testing."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("⚙️  Starting mock data population..."))
        created = {}

        with transaction.atomic():
            # 1. Specialties
            specialties = []
            names = ['Cardiology', 'Dermatology', 'Pediatrics', 'General Practice', 'Neurology', 'Oncology', 'Psychiatry']
            for name in names:
                spec = Specialty.objects.create(name=name, description=fake.text())
                specialties.append(spec)
            created["Specialties"] = len(specialties)

            # 2. Users
            users = []
            for _ in range(20):
                user = User.objects.create(
                    email=fake.unique.email(),
                    username=fake.unique.user_name(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    address=fake.address(),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    phone_number=fake.unique.phone_number(),
                )
                users.append(user)
            created["Users"] = len(users)

            # 3. Doctors
            doctors = []
            for i in range(8):
                doc_user = users[i]
                doctor = Doctor.objects.create(
                    user=doc_user,
                    first_name=doc_user.first_name,
                    last_name=doc_user.last_name,
                    gender=random.choice(['M', 'F']),
                    years_of_experience=random.randint(1, 40),
                    education=fake.text(),
                    bio=fake.text(),
                    languages_spoken=','.join(fake.words(nb=3)),
                    consultation_fee=random.uniform(20, 100),
                    is_available_for_virtual=random.choice([True, False]),
                    is_verified=True,
                )
                doctor.specialties.set(random.sample(specialties, k=random.randint(1, 3)))
                doctors.append(doctor)
            created["Doctors"] = len(doctors)

            # 4. Reviews
            for doctor in doctors:
                for _ in range(random.randint(2, 5)):
                    DoctorReview.objects.create(
                        doctor=doctor,
                        user=random.choice(users[8:]),
                        rating=random.randint(1, 5),
                        comment=fake.sentence(),
                    )

            # 5. Availability
            for doctor in doctors:
                for day in range(7):
                    DoctorAvailability.objects.create(
                        doctor=doctor,
                        day_of_week=day,
                        start_time=timezone.now().replace(hour=9, minute=0, second=0),
                        end_time=timezone.now().replace(hour=17, minute=0, second=0),
                        is_available=True,
                    )

            # 6. Pharmacies
            pharmacies = []
            for _ in range(5):
                pharmacy = Pharmacy.objects.create(
                    name=fake.company(),
                    address=fake.address(),
                    phone_number=fake.phone_number(),
                    email=fake.email(),
                    operating_hours="9am-9pm",
                    is_24_hours=random.choice([True, False]),
                    offers_delivery=random.choice([True, False]),
                    is_active=True,
                )
                pharmacies.append(pharmacy)
            created["Pharmacies"] = len(pharmacies)

            # 7. Medications
            medications = []
            for _ in range(15):
                med = Medication.objects.create(
                    name=fake.word().capitalize(),
                    generic_name=fake.word().capitalize(),
                    description=fake.text(),
                    dosage_form=random.choice(['tablet', 'capsule', 'liquid', 'injection']),
                    strength=f"{random.randint(100, 1000)}mg",
                    manufacturer=fake.company(),
                    requires_prescription=random.choice([True, False]),
                    side_effects=fake.sentence(),
                    contraindications=fake.sentence(),
                    storage_instructions=fake.sentence(),
                )
                medications.append(med)
            created["Medications"] = len(medications)

            # 8. Pharmacy Inventory
            for pharmacy in pharmacies:
                for med in random.sample(medications, k=10):
                    PharmacyInventory.objects.create(
                        pharmacy=pharmacy,
                        medication=med,
                        in_stock=True,
                        quantity=random.randint(10, 200),
                        price=random.uniform(5, 100),
                    )

            # 9. Appointments
            appointments = []
            for _ in range(25):
                user = random.choice(users)
                doctor = random.choice(doctors)
                date = timezone.now().date() - timedelta(days=random.randint(0, 30))
                start_time = timezone.now().replace(hour=random.randint(8, 15), minute=0, second=0)
                end_time = start_time + timedelta(hours=1)
                appt = Appointment.objects.create(
                    user=user,
                    doctor=doctor,
                    date=date,
                    start_time=start_time.time(),
                    end_time=end_time.time(),
                    appointment_type=random.choice(['in_person', 'virtual']),
                    status=random.choice(['scheduled', 'confirmed', 'completed', 'cancelled']),
                    reason=fake.sentence(),
                    notes=fake.sentence(),
                )
                appointments.append(appt)
            created["Appointments"] = len(appointments)

            # 10. Prescriptions
            prescriptions = []
            for appt in appointments:
                pres = Prescription.objects.create(
                    appointment=appt,
                    user=appt.user,
                    doctor=appt.doctor,
                    diagnosis=fake.sentence(),
                    notes=fake.sentence(),
                )
                prescriptions.append(pres)
                for _ in range(random.randint(1, 4)):
                    med = random.choice(medications)
                    PrescriptionItem.objects.create(
                        prescription=pres,
                        medication=med,
                        medication_name=med.name,
                        dosage=f"{random.randint(1, 2)} tablet(s)",
                        frequency=random.choice(['once daily', 'twice daily', 'every 8 hours']),
                        duration=f"{random.randint(3, 14)} days",
                        instructions=fake.sentence(),
                    )
            created["Prescriptions"] = len(prescriptions)

            # 11. Medication Orders
            for user in users:
                for _ in range(random.randint(1, 2)):
                    pharmacy = random.choice(pharmacies)
                    pres = random.choice(prescriptions)
                    order = MedicationOrder.objects.create(
                        user=user,
                        pharmacy=pharmacy,
                        prescription=pres,
                        status=random.choice(['pending', 'ready', 'completed']),
                        is_delivery=random.choice([True, False]),
                        delivery_address=fake.address(),
                        total_amount=random.uniform(20, 200),
                    )
                    for item in pres.items.all():
                        MedicationOrderItem.objects.create(
                            order=order,
                            prescription_item=item,
                            medication_name_text=item.medication_name,
                            dosage_text=item.dosage,
                            quantity=random.randint(1, 3),
                            price_per_unit=random.uniform(5, 50),
                        )

            # 12. Reminders
            for user in users:
                for med in random.sample(medications, k=3):
                    MedicationReminder.objects.create(
                        user=user,
                        medication=med,
                        start_date=timezone.now().date(),
                        end_date=timezone.now().date() + timedelta(days=15),
                        time_of_day=timezone.now().replace(hour=random.randint(6, 22), minute=0, second=0).time(),
                        frequency="daily",
                        dosage=f"{random.randint(1, 2)} tablet(s)",
                        notes=fake.sentence(),
                        is_active=True,
                    )

            # 13. Health Logs
            for user in users:
                for _ in range(5):
                    VitalSign.objects.create(
                        user=user,
                        date_recorded=timezone.now() - timedelta(days=random.randint(0, 30)),
                        heart_rate=random.randint(60, 100),
                        systolic_pressure=random.randint(110, 140),
                        diastolic_pressure=random.randint(70, 90),
                        respiratory_rate=random.randint(12, 20),
                        temperature=round(random.uniform(36.0, 37.5), 1),
                        oxygen_saturation=random.randint(95, 100),
                        notes=fake.sentence(),
                    )
                    SymptomLog.objects.create(
                        user=user,
                        symptom=fake.word(),
                        severity=random.randint(1, 4),
                        duration=f"{random.randint(1, 8)} hours",
                        notes=fake.sentence(),
                    )
                    ExerciseLog.objects.create(
                        user=user,
                        activity_type=random.choice(['Running', 'Cycling', 'Yoga']),
                        duration=random.randint(20, 90),
                        calories_burned=random.randint(100, 600),
                    )
                    SleepLog.objects.create(
                        user=user,
                        sleep_time=timezone.now() - timedelta(hours=8),
                        wake_time=timezone.now(),
                        quality=random.randint(1, 4),
                    )

            # 14. Medical Documents
            for user in users:
                for _ in range(2):
                    MedicalDocument.objects.create(
                        user=user,
                        uploaded_by=user,
                        description=fake.sentence(),
                        document_type=random.choice(['Lab Result', 'Scan', 'Report']),
                    )

            # 15. Insurance Providers & Plans
            providers = []
            for _ in range(3):
                prov = InsuranceProvider.objects.create(
                    name=fake.company(),
                    description=fake.text(),
                    contact_phone=fake.phone_number(),
                    contact_email=fake.email(),
                    website=fake.url(),
                )
                providers.append(prov)

            plans = []
            for prov in providers:
                for _ in range(2):
                    plan = InsurancePlan.objects.create(
                        provider=prov,
                        name=fake.word().capitalize(),
                        plan_type=random.choice(['HMO', 'PPO', 'EPO']),
                        monthly_premium=random.uniform(50, 500),
                        annual_deductible=random.uniform(500, 3000),
                        out_of_pocket_max=random.uniform(1000, 7000),
                        coverage_details=fake.text(),
                    )
                    plans.append(plan)

            # 16. User Insurance
            user_insurances = []
            for user in users:
                plan = random.choice(plans)
                ins = UserInsurance.objects.create(
                    user=user,
                    plan=plan,
                    policy_number=fake.unique.bothify("PL####"),
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=365),
                    is_primary=True,
                )
                user_insurances.append(ins)

            # 17. Insurance Claims
            for ins in user_insurances:
                InsuranceClaim.objects.create(
                    user=ins.user,
                    user_insurance=ins,
                    claim_number=fake.unique.bothify("CLM#####"),
                    service_date=timezone.now().date(),
                    provider_name=fake.company(),
                    claimed_amount=random.uniform(100, 2000),
                    status=random.choice(['submitted', 'approved', 'denied']),
                )

            # 18. Insurance Documents
            for ins in user_insurances:
                InsuranceDocument.objects.create(
                    user=ins.user,
                    user_insurance=ins,
                    title=fake.sentence(),
                    document_type=random.choice(['Claim Form', 'Policy Document']),
                )

        # ✅ Print summary
        self.stdout.write(self.style.SUCCESS("\n✅ Mock data population complete!\n"))
        for k, v in created.items():
            self.stdout.write(f" - {k}: {v} created")
