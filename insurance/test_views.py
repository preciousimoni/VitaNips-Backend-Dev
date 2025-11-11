# insurance/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from faker import Faker
import datetime
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()
fake = Faker()

class InsuranceAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email=fake.email(),
            username=fake.email(),
            password='testpassword'
        )
        self.provider = InsuranceProvider.objects.create(name=fake.company())
        self.plan = InsurancePlan.objects.create(
            provider=self.provider,
            name='Gold Plan',
            plan_type='PPO',
            monthly_premium=500,
            annual_deductible=1000,
            out_of_pocket_max=5000,
            description='A great plan'
        )
        self.user_insurance = UserInsurance.objects.create(
            user=self.user,
            plan=self.plan,
            policy_number=fake.uuid4(),
            member_id=fake.uuid4(),
            start_date=datetime.date.today()
        )
        self.client.force_authenticate(user=self.user)

    def test_list_insurance_providers(self):
        url = reverse('insurance-provider-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_insurance_plans(self):
        url = reverse('insurance-plan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_user_insurance(self):
        url = reverse('user-insurance-list')
        data = {
            'plan_id': self.plan.pk,
            'policy_number': fake.uuid4(),
            'member_id': fake.uuid4(),
            'start_date': datetime.date.today()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserInsurance.objects.count(), 2)

    def test_create_insurance_claim(self):
        url = reverse('insurance-claim-list')
        data = {
            'user_insurance_id': self.user_insurance.pk,
            'claim_number': fake.uuid4(),
            'service_date': datetime.date.today(),
            'provider_name': fake.company(),
            'service_description': 'Annual Checkup',
            'claimed_amount': 250.00,
            'date_submitted': datetime.date.today()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InsuranceClaim.objects.count(), 1)

    def test_create_insurance_document(self):
        url = reverse('insurance-document-list')
        test_file = SimpleUploadedFile("eob.pdf", b"file_content", content_type="application/pdf")
        data = {
            'user_insurance_id': self.user_insurance.pk,
            'title': 'Explanation of Benefits',
            'document_type': 'eob',
            'document': test_file
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InsuranceDocument.objects.count(), 1)
