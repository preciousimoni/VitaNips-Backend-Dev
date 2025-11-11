# insurance/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from faker import Faker
import datetime
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument

User = get_user_model()
fake = Faker()

class InsuranceModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.provider = InsuranceProvider.objects.create(
            name=fake.company()
        )
        self.plan = InsurancePlan.objects.create(
            provider=self.provider,
            name='Gold Plan',
            plan_type='PPO',
            monthly_premium=500,
            annual_deductible=1000,
            out_of_pocket_max=5000
        )
        self.user_insurance = UserInsurance.objects.create(
            user=self.user,
            plan=self.plan,
            policy_number=fake.uuid4(),
            member_id=fake.uuid4(),
            start_date=datetime.date.today()
        )

    def test_create_insurance_provider(self):
        self.assertEqual(InsuranceProvider.objects.count(), 1)
        self.assertEqual(str(self.provider), self.provider.name)

    def test_create_insurance_plan(self):
        self.assertEqual(InsurancePlan.objects.count(), 1)
        self.assertEqual(str(self.plan), f"{self.provider.name} - {self.plan.name}")

    def test_create_user_insurance(self):
        self.assertEqual(UserInsurance.objects.count(), 1)
        self.assertEqual(str(self.user_insurance), f"{self.user.email} - {self.plan}")

    def test_create_insurance_claim(self):
        claim = InsuranceClaim.objects.create(
            user=self.user,
            user_insurance=self.user_insurance,
            claim_number=fake.uuid4(),
            service_date=datetime.date.today(),
            provider_name=fake.company(),
            service_description='Checkup',
            claimed_amount=200,
            date_submitted=datetime.date.today()
        )
        self.assertEqual(InsuranceClaim.objects.count(), 1)
        self.assertEqual(str(claim), f"Claim {claim.claim_number} - {self.user.email}")

    def test_create_insurance_document(self):
        doc = InsuranceDocument.objects.create(
            user=self.user,
            user_insurance=self.user_insurance,
            title='EOB',
            document_type='eob'
        )
        self.assertEqual(InsuranceDocument.objects.count(), 1)
        self.assertEqual(str(doc), f"{doc.title} - {self.user.email}")
