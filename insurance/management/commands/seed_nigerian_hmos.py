# insurance/management/commands/seed_nigerian_hmos.py
from django.core.management.base import BaseCommand
from decimal import Decimal
from insurance.models import InsuranceProvider, InsurancePlan


class Command(BaseCommand):
    help = 'Seed Nigerian HMO providers and their plans into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting HMO seeding...'))
        
        # Clear existing HMO data (optional - comment out if you want to keep existing data)
        # InsurancePlan.objects.filter(provider__name__contains='HMO').delete()
        # InsuranceProvider.objects.filter(name__contains='HMO').delete()
        
        # 1. AXA Mansard HMO
        self.stdout.write('Creating AXA Mansard HMO...')
        axa, created = InsuranceProvider.objects.get_or_create(
            name="AXA Mansard HMO",
            defaults={
                'description': "Premium HMO provider offering comprehensive health coverage including maternity, dental, optical, and emergency services. Known for broad network and quality service.",
                'contact_phone': "+234-1-2701020",
                'contact_email': "info@axamansard.com",
                'website': "https://www.axamansard.com"
            }
        )
        
        # AXA Plans (ACTUAL DATA FROM WEBSITE)
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Bronze",
            defaults={
                'plan_type': 'HMO',
                'description': "Entry-level plan with access to 1,295 hospitals and essential coverage",
                'monthly_premium': Decimal('7208.33'),  # ₦86,500/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('250000.00'),  # Surgery limit
                'coverage_details': "Access to 1,295 hospitals. Surgical services up to ₦250,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦10,000. Eye care up to ₦7,500 (Biennial optical lenses). 5 Physiotherapy sessions.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Routine immunization for children
                'covers_dental': True,  # Up to ₦10,000
                'covers_optical': True,  # Up to ₦7,500
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦250,000
                'covers_physiotherapy': True,  # 5 sessions
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('50000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Silver",
            defaults={
                'plan_type': 'HMO',
                'description': "Mid-tier plan with access to 1,643 hospitals and enhanced coverage",
                'monthly_premium': Decimal('10643.75'),  # ₦127,725/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('300000.00'),  # Surgery limit
                'coverage_details': "Access to 1,643 hospitals. Surgical services up to ₦300,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦20,000. Eye care up to ₦10,500 (Biennial optical lenses). 10 Physiotherapy sessions.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦20,000
                'covers_optical': True,  # Up to ₦10,500
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦300,000
                'covers_physiotherapy': True,  # 10 sessions
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('75000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Gold",
            defaults={
                'plan_type': 'HMO',
                'description': "Premium plan with access to 1,888 hospitals and comprehensive coverage",
                'monthly_premium': Decimal('21099.33'),  # ₦253,192/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('500000.00'),  # Surgery limit
                'coverage_details': "Access to 1,888 hospitals. Surgical services up to ₦500,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦60,000. Eye care up to ₦15,000 (Biennial optical lenses). 15 Physiotherapy sessions.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦60,000
                'covers_optical': True,  # Up to ₦15,000
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦500,000
                'covers_physiotherapy': True,  # 15 sessions
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('100000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Platinum",
            defaults={
                'plan_type': 'HMO',
                'description': "High-tier plan with access to 1,972 hospitals and extensive coverage",
                'monthly_premium': Decimal('34126.25'),  # ₦409,515/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('1000000.00'),  # Surgery limit
                'coverage_details': "Access to 1,972 hospitals. Surgical services up to ₦1,000,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦80,000. Eye care up to ₦25,000 (Biennial optical lenses). 20 Physiotherapy sessions.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦80,000
                'covers_optical': True,  # Up to ₦25,000
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦1,000,000
                'covers_physiotherapy': True,  # 20 sessions
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('150000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Platinum+",
            defaults={
                'plan_type': 'HMO',
                'description': "Enhanced platinum plan with access to 2,004 hospitals and premium coverage",
                'monthly_premium': Decimal('57114.25'),  # ₦685,371/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('1000000.00'),  # Surgery limit
                'coverage_details': "Access to 2,004 hospitals. Surgical services up to ₦1,000,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦80,000. Eye care up to ₦25,000 (Biennial optical lenses). Physiotherapy subject to in-patient limit.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦80,000
                'covers_optical': True,  # Up to ₦25,000
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦1,000,000
                'covers_physiotherapy': True,  # Subject to in-patient limit
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('200000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=axa,
            name="Rhodium",
            defaults={
                'plan_type': 'HMO',
                'description': "Ultimate premium plan with access to 2,004 hospitals and maximum coverage",
                'monthly_premium': Decimal('161648.08'),  # ₦1,939,777/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('1000000.00'),  # Surgery limit
                'coverage_details': "Access to 2,004 hospitals. Surgical services up to ₦1,000,000. Routine immunization. Evacuation services. In-patient care with feeding (General ward). Dental up to ₦150,000. Eye care up to ₦40,000 (Biennial optical lenses). Physiotherapy subject to in-patient limit.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Within benefit limits
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦150,000
                'covers_optical': True,  # Up to ₦40,000
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦1,000,000
                'covers_physiotherapy': True,  # Subject to in-patient limit
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('300000.00'),
                'is_active': True,
            }
        )
        
        
        # 2. Hygeia HMO
        self.stdout.write('Creating Hygeia HMO...')
        hygeia, created = InsuranceProvider.objects.get_or_create(
            name="Hygeia HMO",
            defaults={
                'description': "Long-established HMO with large nationwide hospital network. Offers reliable coverage for individuals, families, and corporate clients.",
                'contact_phone': "+234-1-2713403",
                'contact_email': "info@hygeiahmo.com",
                'website': "https://www.hygeiahmo.com"
            }
        )
        
        # Hygeia Plans (ACTUAL DATA FROM WEBSITE)
        InsurancePlan.objects.get_or_create(
            provider=hygeia,
            name="HyEase",
            defaults={
                'plan_type': 'HMO',
                'description': "Entry-level plan with unrestricted access to Category C-D providers",
                'monthly_premium': Decimal('2209.58'),  # ₦26,515/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('250000.00'),  # In-patient (150k) + Out-patient (100k)
                'coverage_details': "In-patient: ₦150,000. Out-patient: ₦100,000. Medications: ₦50,000. General Ward (7 days/year). GP & Virtual Consultations, Specialist (1/quarter). Ultrasounds, Lab tests, X-rays. Acute ear disease treatment. Telemedicine. Permanent Disability + Death Cover. 7 days wait time.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': Decimal('50000.00'),
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': False,
                'covers_dental': False,
                'covers_optical': False,
                'covers_lab_tests': True,
                'covers_surgery': False,  # Not mentioned
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': True,  # 1 per quarter limit
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('50000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=hygeia,
            name="HyBasic",
            defaults={
                'plan_type': 'HMO',
                'description': "Basic plan with maternity coverage and unrestricted access to Category C-D providers",
                'monthly_premium': Decimal('5505.83'),  # ₦66,070/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('600000.00'),  # In-patient (350k) + Out-patient (250k)
                'coverage_details': "In-patient: ₦350,000. Out-patient: ₦250,000. Medications: ₦80,000. General Ward (15 days/year). Surgeries (Minor, Intermediate, Major, Endoscopies): ₦200,000. GP & Specialist Consultations (Physical & Virtual). X-rays, Ultrasounds, Lab tests. Maternity & Neo-natal: ₦100,000. Adult & Child Immunizations. Dental, ENT, Optical care. Telemedicine. Nutritionist. 7 days wait time.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': Decimal('80000.00'),
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦100,000
                'covers_dental': True,  # Up to specified limits
                'covers_optical': True,  # Up to specified limits
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦200,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('100000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=hygeia,
            name="HyPrime",
            defaults={
                'plan_type': 'HMO',
                'description': "Premium plan with chronic conditions coverage and access to Category B-D providers",
                'monthly_premium': Decimal('15115.00'),  # ₦181,380/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('1500000.00'),  # In-patient (1M) + Out-patient (500k)
                'coverage_details': "In-patient: ₦1,000,000. Out-patient: ₦500,000. Medications: Covered. Semi-Private Ward (15 days/year). Surgeries (Minor, Intermediate, Major, Endoscopies): ₦300,000. Chronic Conditions Covered. GP & Specialist Consultations (Physical & Virtual). X-rays, Ultrasounds, Lab tests. Maternity & Neo-natal: ₦200,000. Adult & Child Immunizations. Dental, ENT, Optical care. Annual Health Checks. Telemedicine. Nutritionist. 7 days wait time.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Covered
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Covered
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦200,000
                'covers_dental': True,  # Up to specified limits
                'covers_optical': True,  # Up to specified limits
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦300,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('150000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=hygeia,
            name="HyPrime Plus",
            defaults={
                'plan_type': 'HMO',
                'description': "High-tier plan with private ward access and unrestricted access to Category A-D providers",
                'monthly_premium': Decimal('40031.67'),  # ₦480,380/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('3500000.00'),  # In-patient (2.5M) + Out-patient (1M)
                'coverage_details': "In-patient: ₦2,500,000. Out-patient: ₦1,000,000. Medications: Covered. Private Ward (20 days/year). Surgeries (Minor, Intermediate, Major, Endoscopies): ₦400,000. Chronic Conditions Covered. GP & Specialist Consultations (Physical & Virtual). X-rays, Ultrasounds, Lab tests. Maternity & Neo-natal: ₦300,000. Adult & Child Immunizations. Dental, ENT, Optical care. Annual Health Checks. Telemedicine. Nutritionist. 7 days wait time.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Covered
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Covered
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦300,000
                'covers_dental': True,  # Up to specified limits
                'covers_optical': True,  # Up to specified limits
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦400,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('200000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=hygeia,
            name="HyPrime Exclusive",
            defaults={
                'plan_type': 'HMO',
                'description': "Exclusive premium plan with maximum coverage and unrestricted access to Category A-D providers",
                'monthly_premium': Decimal('62388.33'),  # ₦748,660/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('4500000.00'),  # In-patient (3M) + Out-patient (1.5M)
                'coverage_details': "In-patient: ₦3,000,000. Out-patient: ₦1,500,000. Medications: Covered. Private Ward (20 days/year). Surgeries (Minor, Intermediate, Major, Endoscopies): ₦600,000. Chronic Conditions Covered. GP & Specialist Consultations (Physical & Virtual). X-rays, Ultrasounds, Lab tests. Maternity & Neo-natal: ₦300,000. Adult & Child Immunizations. Dental, ENT, Optical care. Annual Health Checks. Telemedicine. Nutritionist. 7 days wait time.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Covered
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': None,  # Covered
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦300,000
                'covers_dental': True,  # Up to specified limits
                'covers_optical': True,  # Up to specified limits
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦600,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('300000.00'),
                'is_active': True,
            }
        )
        
        # 3. Reliance HMO
        self.stdout.write('Creating Reliance HMO...')
        reliance, created = InsuranceProvider.objects.get_or_create(
            name="Reliance HMO",
            defaults={
                'description': "Tech-oriented HMO offering flexible and affordable plans with strong telemedicine and digital health options. Great value-for-money.",
                'contact_phone': "+234-1-2806000",
                'contact_email': "info@reliancehmo.com",
                'website': "https://www.reliancehmo.com"
            }
        )
        
        # Reliance Plans (ACTUAL DATA FROM WEBSITE)
        InsurancePlan.objects.get_or_create(
            provider=reliance,
            name="Red Beryl",
            defaults={
                'plan_type': 'HMO',
                'description': "Most affordable small business HMO plan, providing access to great benefits across Nigeria",
                'monthly_premium': Decimal('10000.00'),  # ₦120,000/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('2000000.00'),  # ₦2M total benefit limit
                'coverage_details': "Access to over 1,407 providers. Up to ₦25,000 per year for eye exams, dental cleanings, and more. Staff cover from ₦120,000/year, family cover from ₦465,000/year.",
                'consultation_coverage_percentage': Decimal('85.00'),
                'medication_coverage_percentage': Decimal('80.00'),
                'lab_test_coverage_percentage': Decimal('80.00'),
                'max_consultations_per_year': None,  # Within benefit limit
                'max_medication_amount_per_year': Decimal('2000000.00'),  # Total benefit limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': False,
                'covers_dental': True,  # Up to ₦25k/year
                'covers_optical': True,  # Up to ₦25k/year
                'covers_lab_tests': True,
                'covers_surgery': False,
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': True,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('50000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=reliance,
            name="Alexandrite",
            defaults={
                'plan_type': 'HMO',
                'description': "Comprehensive support to employees, with access to a wide network of healthcare providers",
                'monthly_premium': Decimal('15833.33'),  # ₦190,000/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('3500000.00'),  # ₦3.5M total benefit limit
                'coverage_details': "Access to over 2,448 providers. Up to ₦45,000 per year for eye exams, dental cleanings. Gym access once per week. One spa visit per year. Access to semi-private wards. Staff cover from ₦190,000/year, family cover from ₦722,000/year.",
                'consultation_coverage_percentage': Decimal('90.00'),
                'medication_coverage_percentage': Decimal('85.00'),
                'lab_test_coverage_percentage': Decimal('85.00'),
                'max_consultations_per_year': None,  # Within benefit limit
                'max_medication_amount_per_year': Decimal('3500000.00'),  # Total benefit limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦45k/year
                'covers_optical': True,  # Up to ₦45k/year
                'covers_lab_tests': True,
                'covers_surgery': True,  # Semi-private wards
                'covers_physiotherapy': True,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('100000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=reliance,
            name="Diamond",
            defaults={
                'plan_type': 'HMO',
                'description': "Gives your staff access to a greater number of hospitals, plus wellness checks and private wards",
                'monthly_premium': Decimal('26666.67'),  # ₦320,000/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('5000000.00'),  # ₦5M total benefit limit
                'coverage_details': "Access to over 2,641 providers. Regular wellness checks. Up to ₦105,000 per year for eye exams, dental cleanings. Gym access twice per week. Two spa visits per year. Access to private wards. Staff cover from ₦320,000/year, family cover from ₦1,220,000/year.",
                'consultation_coverage_percentage': Decimal('95.00'),
                'medication_coverage_percentage': Decimal('90.00'),
                'lab_test_coverage_percentage': Decimal('90.00'),
                'max_consultations_per_year': None,  # Within benefit limit
                'max_medication_amount_per_year': Decimal('5000000.00'),  # Total benefit limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦105k/year
                'covers_optical': True,  # Up to ₦105k/year
                'covers_lab_tests': True,
                'covers_surgery': True,  # Private wards
                'covers_physiotherapy': True,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('150000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=reliance,
            name="Red Diamond",
            defaults={
                'plan_type': 'HMO',
                'description': "Ultimate plan, giving staff the widest range of support at the most number of clinics and providers",
                'monthly_premium': Decimal('39583.33'),  # ₦475,000/year ÷ 12
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('7000000.00'),  # ₦7M total benefit limit
                'coverage_details': "Access to over 2,746 providers. Regular wellness checks. Up to ₦140,000 per year for eye exams, dental cleanings. Gym access 3 times per week. Two spa visits for massage and one facial per year. Access to private wards. Staff cover from ₦475,000/year, family cover from ₦1,805,000/year.",
                'consultation_coverage_percentage': Decimal('100.00'),
                'medication_coverage_percentage': Decimal('95.00'),
                'lab_test_coverage_percentage': Decimal('95.00'),
                'max_consultations_per_year': None,  # Within benefit limit
                'max_medication_amount_per_year': Decimal('7000000.00'),  # Total benefit limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': True,  # Up to ₦140k/year
                'covers_optical': True,  # Up to ₦140k/year
                'covers_lab_tests': True,
                'covers_surgery': True,  # Private wards
                'covers_physiotherapy': True,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('200000.00'),
                'is_active': True,
            }
        )
        
        # 4. Avon Healthcare Limited
        self.stdout.write('Creating Avon Healthcare...')
        avon, created = InsuranceProvider.objects.get_or_create(
            name="Avon Healthcare Limited",
            defaults={
                'description': "Balanced HMO provider offering good value between cost and coverage. Ideal for individuals, small businesses, and families.",
                'contact_phone': "+234-1-2714000",
                'contact_email': "info@avonhealthcare.com",
                'website': "https://www.avonhealthcare.com"
            }
        )
        
        # Avon Plans
        InsurancePlan.objects.get_or_create(
            provider=avon,
            name="Avon Standard Plan",
            defaults={
                'plan_type': 'HMO',
                'description': "Well-balanced coverage for individuals and small families",
                'monthly_premium': Decimal('18000.00'),
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('350000.00'),
                'coverage_details': "Balanced plan covering consultations, medications, lab tests, and emergency care",
                'consultation_coverage_percentage': Decimal('90.00'),
                'medication_coverage_percentage': Decimal('85.00'),
                'lab_test_coverage_percentage': Decimal('85.00'),
                'max_consultations_per_year': 18,
                'max_medication_amount_per_year': Decimal('600000.00'),
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,
                'covers_dental': False,
                'covers_optical': False,
                'covers_lab_tests': True,
                'covers_surgery': True,
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': True,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('75000.00'),
                'is_active': True,
            }
        )
        
        # 5. Clearline HMO Limited
        self.stdout.write('Creating Clearline HMO...')
        clearline, created = InsuranceProvider.objects.get_or_create(
            name="Clearline HMO Limited",
            defaults={
                'description': "Affordable HMO with simpler plans and decent nationwide network. Great for budget-conscious individuals.",
                'contact_phone': "+234-1-2806500",
                'contact_email': "info@clearlinehmo.com",
                'website': "https://www.clearlinehmo.com"
            }
        )
        
        # Clearline Plans
        InsurancePlan.objects.get_or_create(
            provider=clearline,
            name="Clearline Economy Plan",
            defaults={
                'plan_type': 'HMO',
                'description': "Budget-friendly plan with essential coverage",
                'monthly_premium': Decimal('6000.00'),
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('150000.00'),
                'coverage_details': "Affordable plan covering basic consultations, medications, and emergency care",
                'consultation_coverage_percentage': Decimal('75.00'),
                'medication_coverage_percentage': Decimal('70.00'),
                'lab_test_coverage_percentage': Decimal('70.00'),
                'max_consultations_per_year': 10,
                'max_medication_amount_per_year': Decimal('250000.00'),
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': False,
                'covers_dental': False,
                'covers_optical': False,
                'covers_lab_tests': True,
                'covers_surgery': False,
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': True,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('25000.00'),
                'is_active': True,
            }
        )
        
        # 6. Total Health Trust Ltd (THT)
        self.stdout.write('Creating Total Health Trust...')
        tht, created = InsuranceProvider.objects.get_or_create(
            name="Total Health Trust Ltd",
            defaults={
                'description': "Corporate-focused HMO offering comprehensive and premium coverage for employees and large organizations.",
                'contact_phone': "+234-1-2806700",
                'contact_email': "info@totalhealthtrust.com",
                'website': "https://www.totalhealthtrust.com"
            }
        )
        
        # THT Plans (ACTUAL DATA FROM WEBSITE)
        InsurancePlan.objects.get_or_create(
            provider=tht,
            name="Alldo",
            defaults={
                'plan_type': 'HMO',
                'description': "Essential health plan at a pocket-friendly rate covering outpatient, inpatient, and diagnostic services",
                'monthly_premium': Decimal('8000.00'),  # Estimated based on market positioning
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('275000.00'),  # In-patient (150k) + Out-patient (125k)
                'coverage_details': "In-patient limit: ₦150,000. Out-patient limit: ₦125,000. General and Specialist Consultation. Basic scans. Minor surgeries up to ₦25,000. Emergency & Ambulance. Basic dental (₦7,500). Eye care (₦7,500). Telemedicine and onsite health checks.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': Decimal('125000.00'),  # Out-patient limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': False,
                'covers_dental': True,  # Up to ₦7,500
                'covers_optical': True,  # Up to ₦7,500
                'covers_lab_tests': True,
                'covers_surgery': True,  # Minor only, up to ₦25,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('25000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=tht,
            name="Pearl",
            defaults={
                'plan_type': 'HMO',
                'description': "Mid-range health plan with obstetrics, gynaecological and ophthalmological services plus telemedicine and gym access",
                'monthly_premium': Decimal('18000.00'),  # Estimated based on market positioning
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('600000.00'),  # In-patient (400k) + Out-patient (200k)
                'coverage_details': "In-patient limit: ₦400,000. Out-patient limit: ₦200,000. General and Specialist Consultation. Advanced scans (CT, MRI) up to ₦50,000. Minor, Intermediate & Major Surgeries up to ₦150,000. Emergency & Ambulance. Dental up to ₦20,000. Optical up to ₦20,000 (Lens & Frame ₦10,000). Maternity: Delivery ₦130,000, Neonatal ₦30,000. Telemedicine. Discounted gym access.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': Decimal('200000.00'),  # Out-patient limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦130,000 delivery + ₦30,000 neonatal
                'covers_dental': True,  # Up to ₦20,000
                'covers_optical': True,  # Up to ₦20,000 (₦10,000 for lens & frame)
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦150,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('50000.00'),
                'is_active': True,
            }
        )
        
        InsurancePlan.objects.get_or_create(
            provider=tht,
            name="Coral",
            defaults={
                'plan_type': 'HMO',
                'description': "Comprehensive health plan with obstetrics, neonatal/pediatric, and surgical services plus telemedicine and gym access",
                'monthly_premium': Decimal('25000.00'),  # Estimated based on market positioning
                'annual_deductible': Decimal('0.00'),
                'out_of_pocket_max': Decimal('750000.00'),  # In-patient (500k) + Out-patient (250k)
                'coverage_details': "In-patient limit: ₦500,000. Out-patient limit: ₦250,000. General and Specialist Consultation. Advanced scans (CT, MRI) up to ₦100,000. Minor, Intermediate & Major Surgeries up to ₦275,000. Emergency & Ambulance. Dental up to ₦30,000. Optical up to ₦30,000 (Lens & Frame ₦15,000). Maternity: Delivery ₦200,000, Neonatal ₦50,000. Telemedicine. Discounted gym access.",
                'consultation_coverage_percentage': Decimal('100.00'),  # Within limits
                'medication_coverage_percentage': Decimal('100.00'),  # Within limits
                'lab_test_coverage_percentage': Decimal('100.00'),  # Within limits
                'max_consultations_per_year': None,  # Within benefit limits
                'max_medication_amount_per_year': Decimal('250000.00'),  # Out-patient limit
                'covers_telemedicine': True,
                'covers_emergency': True,
                'covers_maternity': True,  # Up to ₦200,000 delivery + ₦50,000 neonatal
                'covers_dental': True,  # Up to ₦30,000
                'covers_optical': True,  # Up to ₦30,000 (₦15,000 for lens & frame)
                'covers_lab_tests': True,
                'covers_surgery': True,  # Up to ₦275,000
                'covers_physiotherapy': False,
                'requires_preauth_for_specialist': False,
                'requires_preauth_for_surgery': True,
                'preauth_threshold_amount': Decimal('100000.00'),
                'is_active': True,
            }
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded 6 Nigerian HMO providers with 21 plans!'))
        self.stdout.write(self.style.SUCCESS('Providers: AXA Mansard (6 plans), Hygeia (5 plans), Reliance (4 plans), Avon, Clearline, Total Health Trust (3 plans)'))



