from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctors.models import Doctor, Specialty, DoctorReview, DoctorAvailability, Appointment, Prescription, PrescriptionItem
from pharmacy.models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder
from health.models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument
from insurance.models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument
from users.models import MedicalHistory, Vaccination
import random
from faker import Faker
from django.utils import timezone
from datetime import timedelta

fake = Faker()
User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with comprehensive mock data for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting mock data population...'))
        
        # 1. Create Specialties
        self.stdout.write('Creating specialties...')
        specialties = []
        specialty_names = ['Cardiology', 'Dermatology', 'Pediatrics', 'General Practice', 'Neurology', 'Oncology', 'Psychiatry', 'Orthopedics']
        for name in specialty_names:
            spec, created = Specialty.objects.get_or_create(
                name=name,
                defaults={'description': fake.text(max_nb_chars=200)}
            )
            specialties.append(spec)
            if created:
                self.stdout.write(f'  ✓ Created specialty: {name}')
        
        # 2. Create Users
        self.stdout.write('Creating users...')
        users = []
        for i in range(20):
            try:
                user = User.objects.create_user(
                    email=f'user{i}_{fake.user_name()}@example.com',
                    username=f'user{i}_{fake.user_name()}',
                    password='password123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    address=fake.address(),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    phone_number=f'+1{random.randint(2000000000, 9999999999)}',
                    blood_group=random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
                    weight=round(random.uniform(50, 100), 2),
                    height=round(random.uniform(150, 200), 2),
                )
                users.append(user)
                self.stdout.write(f'  ✓ Created user: {user.email}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Skipped user creation: {e}'))
        
        # 3. Create Doctors
        self.stdout.write('Creating doctors...')
        doctors = []
        for i in range(min(8, len(users))):
            doc_user = users[i]
            doctor, created = Doctor.objects.get_or_create(
                user=doc_user,
                defaults={
                    'first_name': doc_user.first_name,
                    'last_name': doc_user.last_name,
                    'gender': random.choice(['M', 'F']),
                    'years_of_experience': random.randint(1, 40),
                    'education': fake.text(max_nb_chars=200),
                    'bio': fake.text(max_nb_chars=300),
                    'languages_spoken': ','.join(random.sample(['English', 'French', 'Spanish', 'German'], k=2)),
                    'consultation_fee': round(random.uniform(20, 150), 2),
                    'is_available_for_virtual': random.choice([True, False]),
                    'is_verified': True,
                }
            )
            if created:
                doctor.specialties.set(random.sample(specialties, k=random.randint(1, 3)))
                doctors.append(doctor)
                self.stdout.write(f'  ✓ Created doctor: Dr. {doctor.first_name} {doctor.last_name}')
        
        # 4. Doctor Reviews
        self.stdout.write('Creating doctor reviews...')
        review_count = 0
        for doctor in doctors:
            for _ in range(random.randint(2, 6)):
                reviewer = random.choice(users[len(doctors):]) if len(users) > len(doctors) else random.choice(users)
                review, created = DoctorReview.objects.get_or_create(
                    doctor=doctor,
                    user=reviewer,
                    defaults={
                        'rating': random.randint(3, 5),
                        'comment': fake.sentence(),
                    }
                )
                if created:
                    review_count += 1
        self.stdout.write(f'  ✓ Created {review_count} reviews')
        
        # 5. Doctor Availability
        self.stdout.write('Creating doctor availability...')
        avail_count = 0
        for doctor in doctors:
            for day in range(7):
                avail, created = DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    defaults={
                        'start_time': timezone.now().replace(hour=9, minute=0, second=0).time(),
                        'end_time': timezone.now().replace(hour=17, minute=0, second=0).time(),
                        'is_available': True,
                    }
                )
                if created:
                    avail_count += 1
        self.stdout.write(f'  ✓ Created {avail_count} availability slots')
        
        # 6. Pharmacies
        self.stdout.write('Creating pharmacies...')
        pharmacies = []
        for i in range(5):
            pharmacy, created = Pharmacy.objects.get_or_create(
                name=f"{fake.company()} Pharmacy",
                defaults={
                    'address': fake.address(),
                    'phone_number': f'+1{random.randint(2000000000, 9999999999)}',
                    'email': f'pharmacy{i}@example.com',
                    'operating_hours': '9am-9pm',
                    'is_24_hours': random.choice([True, False]),
                    'offers_delivery': random.choice([True, False]),
                    'is_active': True,
                }
            )
            pharmacies.append(pharmacy)
            if created:
                self.stdout.write(f'  ✓ Created pharmacy: {pharmacy.name}')
        
        # 7. Medications
        self.stdout.write('Creating medications...')
        medications = []
        med_names = ['Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Metformin', 'Lisinopril', 
                     'Atorvastatin', 'Omeprazole', 'Levothyroxine', 'Azithromycin', 'Ciprofloxacin',
                     'Aspirin', 'Prednisone', 'Losartan', 'Gabapentin', 'Hydrochlorothiazide']
        for name in med_names:
            med, created = Medication.objects.get_or_create(
                name=name,
                defaults={
                    'generic_name': name.lower(),
                    'description': fake.text(max_nb_chars=200),
                    'dosage_form': random.choice(['tablet', 'capsule', 'liquid', 'injection']),
                    'strength': f"{random.choice([100, 250, 500, 1000])}mg",
                    'manufacturer': fake.company(),
                    'requires_prescription': random.choice([True, False]),
                    'side_effects': fake.sentence(),
                    'contraindications': fake.sentence(),
                    'storage_instructions': 'Store in a cool, dry place',
                }
            )
            medications.append(med)
            if created:
                self.stdout.write(f'  ✓ Created medication: {name}')
        
        # 8. Pharmacy Inventory
        self.stdout.write('Creating pharmacy inventory...')
        inventory_count = 0
        for pharmacy in pharmacies:
            for med in random.sample(medications, k=10):
                inv, created = PharmacyInventory.objects.get_or_create(
                    pharmacy=pharmacy,
                    medication=med,
                    defaults={
                        'in_stock': True,
                        'quantity': random.randint(10, 200),
                        'price': round(random.uniform(5, 100), 2),
                    }
                )
                if created:
                    inventory_count += 1
        self.stdout.write(f'  ✓ Created {inventory_count} inventory items')
        
        # 9. Appointments
        self.stdout.write('Creating appointments...')
        appointments = []
        for i in range(30):
            user = random.choice(users)
            doctor = random.choice(doctors)
            date = timezone.now().date() - timedelta(days=random.randint(0, 30))
            start_hour = random.randint(8, 15)
            appointment, created = Appointment.objects.get_or_create(
                user=user,
                doctor=doctor,
                date=date,
                start_time=timezone.now().replace(hour=start_hour, minute=0, second=0).time(),
                defaults={
                    'end_time': timezone.now().replace(hour=start_hour + 1, minute=0, second=0).time(),
                    'appointment_type': random.choice(['in_person', 'virtual']),
                    'status': random.choice(['scheduled', 'confirmed', 'completed', 'cancelled']),
                    'reason': fake.sentence(),
                    'notes': fake.sentence(),
                    'followup_required': random.choice([True, False]),
                }
            )
            if created:
                appointments.append(appointment)
        self.stdout.write(f'  ✓ Created {len(appointments)} appointments')
        
        # 10. Prescriptions & Items
        self.stdout.write('Creating prescriptions...')
        prescriptions = []
        for appt in appointments:
            if appt.status == 'completed':
                prescription, created = Prescription.objects.get_or_create(
                    appointment=appt,
                    user=appt.user,
                    doctor=appt.doctor,
                    defaults={
                        'diagnosis': fake.sentence(),
                        'notes': fake.sentence(),
                    }
                )
                if created:
                    prescriptions.append(prescription)
                    # Add prescription items
                    for _ in range(random.randint(1, 4)):
                        med = random.choice(medications)
                        PrescriptionItem.objects.get_or_create(
                            prescription=prescription,
                            medication=med,
                            medication_name=med.name,
                            defaults={
                                'dosage': f"{random.randint(1, 2)} tablet(s)",
                                'frequency': random.choice(['once daily', 'twice daily', 'three times daily', 'every 8 hours']),
                                'duration': f"{random.randint(3, 14)} days",
                                'instructions': fake.sentence(),
                            }
                        )
        self.stdout.write(f'  ✓ Created {len(prescriptions)} prescriptions')
        
        # 11. Medication Orders & Items
        self.stdout.write('Creating medication orders...')
        order_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for _ in range(random.randint(1, 2)):
                if prescriptions:
                    pharmacy = random.choice(pharmacies)
                    prescription = random.choice(prescriptions)
                    order, created = MedicationOrder.objects.get_or_create(
                        user=user,
                        pharmacy=pharmacy,
                        prescription=prescription,
                        defaults={
                            'status': random.choice(['pending', 'processing', 'ready', 'completed']),
                            'is_delivery': random.choice([True, False]),
                            'delivery_address': fake.address(),
                            'total_amount': round(random.uniform(20, 200), 2),
                            'order_date': timezone.now() - timedelta(days=random.randint(0, 30)),
                            'pickup_or_delivery_date': timezone.now() + timedelta(days=random.randint(1, 7)),
                            'notes': fake.sentence(),
                        }
                    )
                    if created:
                        order_count += 1
                        # Add order items
                        for item in prescription.items.all()[:3]:
                            MedicationOrderItem.objects.get_or_create(
                                order=order,
                                prescription_item=item,
                                defaults={
                                    'medication_name_text': item.medication_name,
                                    'dosage_text': item.dosage,
                                    'quantity': random.randint(1, 3),
                                    'price_per_unit': round(random.uniform(5, 50), 2),
                                }
                            )
        self.stdout.write(f'  ✓ Created {order_count} medication orders')
        
        # 12. Medication Reminders
        self.stdout.write('Creating medication reminders...')
        reminder_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for med in random.sample(medications, k=2):
                reminder, created = MedicationReminder.objects.get_or_create(
                    user=user,
                    medication=med,
                    defaults={
                        'start_date': timezone.now().date() - timedelta(days=random.randint(0, 10)),
                        'end_date': timezone.now().date() + timedelta(days=random.randint(5, 30)),
                        'time_of_day': timezone.now().replace(hour=random.randint(8, 20), minute=0, second=0).time(),
                        'frequency': random.choice(['daily', 'weekly']),
                        'dosage': f"{random.randint(1, 2)} tablet(s)",
                        'notes': fake.sentence(),
                        'is_active': True,
                    }
                )
                if created:
                    reminder_count += 1
        self.stdout.write(f'  ✓ Created {reminder_count} medication reminders')
        
        # 13. Health logs
        self.stdout.write('Creating health logs...')
        health_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for _ in range(3):
                # Vital Signs
                VitalSign.objects.create(
                    user=user,
                    date_recorded=timezone.now() - timedelta(days=random.randint(0, 30)),
                    heart_rate=random.randint(60, 100),
                    systolic_pressure=random.randint(110, 140),
                    diastolic_pressure=random.randint(70, 90),
                    respiratory_rate=random.randint(12, 20),
                    temperature=round(random.uniform(36.0, 37.5), 1),
                    oxygen_saturation=random.randint(95, 100),
                    blood_glucose=round(random.uniform(80, 120), 1),
                    weight=round(random.uniform(60, 90), 1),
                    notes=fake.sentence(),
                )
                
                # Symptom Logs
                SymptomLog.objects.create(
                    user=user,
                    symptom=random.choice(['Headache', 'Fever', 'Cough', 'Fatigue', 'Nausea']),
                    date_experienced=timezone.now() - timedelta(days=random.randint(0, 30)),
                    severity=random.randint(1, 4),
                    duration=f"{random.randint(1, 8)} hours",
                    notes=fake.sentence(),
                )
                
                # Food Logs
                FoodLog.objects.create(
                    user=user,
                    food_item=random.choice(['Salad', 'Chicken', 'Rice', 'Pasta', 'Fruit']),
                    meal_type=random.choice(['breakfast', 'lunch', 'dinner', 'snack']),
                    datetime=timezone.now() - timedelta(days=random.randint(0, 7)),
                    calories=random.randint(200, 800),
                    carbohydrates=round(random.uniform(20, 100), 1),
                    proteins=round(random.uniform(5, 40), 1),
                    fats=round(random.uniform(5, 30), 1),
                    notes=fake.sentence(),
                )
                
                # Exercise Logs
                ExerciseLog.objects.create(
                    user=user,
                    activity_type=random.choice(['Running', 'Cycling', 'Swimming', 'Yoga', 'Walking']),
                    datetime=timezone.now() - timedelta(days=random.randint(0, 14)),
                    duration=random.randint(20, 90),
                    calories_burned=random.randint(100, 600),
                    distance=round(random.uniform(1, 10), 1),
                    notes=fake.sentence(),
                )
                
                # Sleep Logs
                sleep_start = timezone.now() - timedelta(days=random.randint(0, 14), hours=8)
                SleepLog.objects.create(
                    user=user,
                    sleep_time=sleep_start,
                    wake_time=sleep_start + timedelta(hours=random.randint(6, 9)),
                    quality=random.randint(1, 4),
                    interruptions=random.randint(0, 3),
                    notes=fake.sentence(),
                )
                
                health_count += 5
        self.stdout.write(f'  ✓ Created {health_count} health log entries')
        
        # 14. Health Goals
        self.stdout.write('Creating health goals...')
        goal_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for _ in range(2):
                HealthGoal.objects.create(
                    user=user,
                    goal_type=random.choice(['weight', 'steps', 'exercise', 'water', 'sleep']),
                    target_value=round(random.uniform(5, 100), 1),
                    unit=random.choice(['kg', 'steps', 'minutes', 'liters', 'hours']),
                    start_date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                    target_date=timezone.now().date() + timedelta(days=random.randint(10, 60)),
                    status=random.choice(['active', 'completed', 'abandoned']),
                    progress=round(random.uniform(0, 100), 1),
                    notes=fake.sentence(),
                )
                goal_count += 1
        self.stdout.write(f'  ✓ Created {goal_count} health goals')
        
        # 15. Insurance Providers & Plans
        self.stdout.write('Creating insurance providers and plans...')
        providers = []
        provider_names = ['HealthCare Plus', 'MediShield', 'VitaCare Insurance']
        for name in provider_names:
            provider, created = InsuranceProvider.objects.get_or_create(
                name=name,
                defaults={
                    'description': fake.text(max_nb_chars=200),
                    'contact_phone': f'+1{random.randint(2000000000, 9999999999)}',
                    'contact_email': f'{name.lower().replace(" ", "")}@example.com',
                    'website': fake.url(),
                }
            )
            providers.append(provider)
            if created:
                self.stdout.write(f'  ✓ Created provider: {name}')
        
        plans = []
        plan_count = 0
        for provider in providers:
            for plan_name in ['Basic', 'Premium']:
                plan, created = InsurancePlan.objects.get_or_create(
                    provider=provider,
                    name=f'{plan_name} Plan',
                    defaults={
                        'plan_type': random.choice(['HMO', 'PPO', 'EPO']),
                        'description': fake.text(max_nb_chars=200),
                        'monthly_premium': round(random.uniform(50, 500), 2),
                        'annual_deductible': round(random.uniform(500, 5000), 2),
                        'out_of_pocket_max': round(random.uniform(1000, 10000), 2),
                        'coverage_details': fake.text(max_nb_chars=200),
                        'is_active': True,
                    }
                )
                plans.append(plan)
                if created:
                    plan_count += 1
        self.stdout.write(f'  ✓ Created {plan_count} insurance plans')
        
        # 16. User Insurance
        self.stdout.write('Creating user insurance records...')
        user_insurances = []
        for user in random.sample(users, k=min(15, len(users))):
            plan = random.choice(plans)
            user_ins, created = UserInsurance.objects.get_or_create(
                user=user,
                plan=plan,
                defaults={
                    'policy_number': fake.bothify(text='POL######'),
                    'group_number': fake.bothify(text='GRP###'),
                    'member_id': fake.bothify(text='MEM######'),
                    'start_date': timezone.now().date() - timedelta(days=random.randint(0, 365)),
                    'end_date': timezone.now().date() + timedelta(days=random.randint(30, 365)),
                    'is_primary': True,
                }
            )
            if created:
                user_insurances.append(user_ins)
        self.stdout.write(f'  ✓ Created {len(user_insurances)} user insurance records')
        
        # 17. Insurance Claims
        self.stdout.write('Creating insurance claims...')
        claim_count = 0
        for user_ins in user_insurances[:10]:
            for _ in range(random.randint(1, 2)):
                InsuranceClaim.objects.create(
                    user=user_ins.user,
                    user_insurance=user_ins,
                    claim_number=fake.bothify(text='CLM######'),
                    service_date=timezone.now().date() - timedelta(days=random.randint(0, 180)),
                    provider_name=fake.company(),
                    service_description=fake.sentence(),
                    claimed_amount=round(random.uniform(100, 2000), 2),
                    approved_amount=round(random.uniform(50, 1500), 2),
                    patient_responsibility=round(random.uniform(0, 500), 2),
                    status=random.choice(['submitted', 'in_review', 'approved', 'paid']),
                    date_submitted=timezone.now().date() - timedelta(days=random.randint(0, 180)),
                    date_processed=timezone.now().date() - timedelta(days=random.randint(0, 90)),
                    notes=fake.sentence(),
                )
                claim_count += 1
        self.stdout.write(f'  ✓ Created {claim_count} insurance claims')
        
        # 18. Medical History
        self.stdout.write('Creating medical history records...')
        history_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for condition in random.sample(['Hypertension', 'Diabetes', 'Asthma', 'Allergy'], k=2):
                MedicalHistory.objects.create(
                    user=user,
                    condition=condition,
                    diagnosis_date=timezone.now().date() - timedelta(days=random.randint(30, 1000)),
                    treatment=fake.sentence(),
                    notes=fake.sentence(),
                    is_active=random.choice([True, False]),
                )
                history_count += 1
        self.stdout.write(f'  ✓ Created {history_count} medical history records')
        
        # 19. Vaccinations
        self.stdout.write('Creating vaccination records...')
        vaccination_count = 0
        for user in random.sample(users, k=min(10, len(users))):
            for vaccine in ['COVID-19', 'Influenza', 'Hepatitis B']:
                Vaccination.objects.create(
                    user=user,
                    vaccine_name=vaccine,
                    date_administered=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    dose_number=random.randint(1, 3),
                    administered_at=fake.company(),
                    batch_number=fake.bothify(text='BATCH###??'),
                    notes=fake.sentence(),
                )
                vaccination_count += 1
        self.stdout.write(f'  ✓ Created {vaccination_count} vaccination records')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Mock data population complete!'))
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  - {len(specialties)} specialties')
        self.stdout.write(f'  - {len(users)} users')
        self.stdout.write(f'  - {len(doctors)} doctors')
        self.stdout.write(f'  - {len(pharmacies)} pharmacies')
        self.stdout.write(f'  - {len(medications)} medications')
        self.stdout.write(f'  - {len(appointments)} appointments')
        self.stdout.write(f'  - {len(prescriptions)} prescriptions')
        self.stdout.write(f'  - Many more related records created!')
        self.stdout.write(self.style.SUCCESS('\n🎉 Database is ready for testing!'))
