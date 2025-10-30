# pharmacy/management/commands/populate_locations.py
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from pharmacy.models import Pharmacy
from emergency.models import EmergencyService


class Command(BaseCommand):
    help = 'Populate geographic locations for pharmacies and emergency services'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating pharmacy locations...')
        
        # Sample coordinates around Lagos, Nigeria (you can adjust these)
        pharmacy_locations = {
            # Format: pharmacy_name_keyword: (latitude, longitude)
            'HealthPlus': (6.5244, 3.3792),  # Victoria Island, Lagos
            'MedPlus': (6.4698, 3.5852),     # Lekki, Lagos
            'Alpha': (6.6018, 3.3515),       # Ikeja, Lagos
            'Juhel': (6.5355, 3.3508),       # Yaba, Lagos
            'Care': (6.4281, 3.4219),        # Ikoyi, Lagos
        }

        pharmacies = Pharmacy.objects.all()
        updated_count = 0
        
        for pharmacy in pharmacies:
            # Try to match pharmacy name with predefined locations
            for keyword, (lat, lon) in pharmacy_locations.items():
                if keyword.lower() in pharmacy.name.lower():
                    pharmacy.location = Point(lon, lat, srid=4326)  # Note: Point(longitude, latitude)
                    pharmacy.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Updated {pharmacy.name} - Location: ({lat}, {lon})'
                    ))
                    updated_count += 1
                    break
            else:
                # If no match, assign a random location in Lagos area
                import random
                lat = 6.4 + random.uniform(0, 0.3)
                lon = 3.3 + random.uniform(0, 0.3)
                pharmacy.location = Point(lon, lat, srid=4326)
                pharmacy.save()
                self.stdout.write(self.style.WARNING(
                    f'Assigned random location to {pharmacy.name} - ({lat:.4f}, {lon:.4f})'
                ))
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nUpdated {updated_count} pharmacies'))

        # Populate Emergency Services
        self.stdout.write('\nPopulating emergency service locations...')
        
        emergency_data = [
            {
                'name': 'Lagos University Teaching Hospital (LUTH)',
                'service_type': 'hospital',
                'address': 'Idi-Araba, Mushin, Lagos',
                'phone_number': '+234 1 5852368',
                'latitude': 6.5123,
                'longitude': 3.3635,
                'is_24_hours': True,
                'has_emergency_room': True,
                'provides_ambulance': True,
            },
            {
                'name': 'Lagos State University Teaching Hospital (LASUTH)',
                'service_type': 'hospital',
                'address': 'Ikeja, Lagos',
                'phone_number': '+234 1 7743667',
                'latitude': 6.6018,
                'longitude': 3.3515,
                'is_24_hours': True,
                'has_emergency_room': True,
                'provides_ambulance': True,
            },
            {
                'name': 'Reddington Hospital',
                'service_type': 'hospital',
                'address': '12 Idowu Martins Street, Victoria Island, Lagos',
                'phone_number': '+234 1 4617000',
                'latitude': 6.4281,
                'longitude': 3.4219,
                'is_24_hours': True,
                'has_emergency_room': True,
                'provides_ambulance': True,
            },
            {
                'name': 'Eko Hospital',
                'service_type': 'hospital',
                'address': '31 Mobolaji Bank Anthony Way, Ikeja, Lagos',
                'phone_number': '+234 1 2797900',
                'latitude': 6.6004,
                'longitude': 3.3547,
                'is_24_hours': True,
                'has_emergency_room': True,
                'provides_ambulance': True,
            },
            {
                'name': 'St. Nicholas Hospital',
                'service_type': 'hospital',
                'address': '57 Campbell Street, Lagos Island, Lagos',
                'phone_number': '+234 1 4617200',
                'latitude': 6.4511,
                'longitude': 3.3887,
                'is_24_hours': True,
                'has_emergency_room': True,
                'provides_ambulance': True,
            },
            {
                'name': 'Lagos Fire Service - Headquarters',
                'service_type': 'fire',
                'address': 'Alausa, Ikeja, Lagos',
                'phone_number': '112',
                'alternative_phone': '+234 1 7613971',
                'latitude': 6.6167,
                'longitude': 3.3577,
                'is_24_hours': True,
            },
            {
                'name': 'Nigeria Police - Lagos State Command',
                'service_type': 'police',
                'address': 'GRA Ikeja, Lagos',
                'phone_number': '112',
                'alternative_phone': '+234 1 4974669',
                'latitude': 6.6126,
                'longitude': 3.3448,
                'is_24_hours': True,
            },
            {
                'name': 'LASAMBUS - Lagos Ambulance Service',
                'service_type': 'ambulance',
                'address': 'Alausa, Ikeja, Lagos',
                'phone_number': '767',
                'alternative_phone': '+234 803 600 6006',
                'latitude': 6.6177,
                'longitude': 3.3567,
                'is_24_hours': True,
                'provides_ambulance': True,
            },
        ]

        created_count = 0
        for data in emergency_data:
            lat = data.pop('latitude')
            lon = data.pop('longitude')
            service, created = EmergencyService.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'location': Point(lon, lat, srid=4326)
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {service.name}'))
                created_count += 1
            else:
                # Update location if exists
                service.location = Point(lon, lat, srid=4326)
                service.save()
                self.stdout.write(self.style.WARNING(f'Updated: {service.name}'))
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nProcessed {created_count} emergency services'
        ))
        self.stdout.write(self.style.SUCCESS('\n✓ Location population complete!'))
