# vitanips/management/commands/enable_postgis.py
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Enable PostGIS extensions in the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                self.stdout.write(self.style.SUCCESS('✓ PostGIS extension enabled'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'PostGIS extension: {e}'))
            
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
                self.stdout.write(self.style.SUCCESS('✓ PostGIS Topology extension enabled'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'PostGIS Topology extension: {e}'))

