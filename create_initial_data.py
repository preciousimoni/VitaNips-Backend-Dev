import os
import django
import sys

# Add the project root to the python path
sys.path.append('/Users/rpublc/Documents/myprojects/VitaNips/VitaNips-Backend-Dev')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from payments.models import PharmacySubscription

def create_data():
    if not PharmacySubscription.objects.filter(tier='standard').exists():
        plan = PharmacySubscription.objects.create(
            name='Standard Pharmacy Registration',
            tier='standard',
            description='Annual registration fee for pharmacies',
            annual_price=50000.00,
            features={'listing': True, 'orders': True}
        )
        print(f"Created Standard Pharmacy Subscription Plan with ID: {plan.id}")
    else:
        plan = PharmacySubscription.objects.get(tier='standard')
        print(f"Standard Pharmacy Subscription Plan already exists with ID: {plan.id}")

if __name__ == '__main__':
    create_data()
