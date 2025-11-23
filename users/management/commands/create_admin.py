# users/management/commands/create_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates or updates the default admin user, resolving potential conflicts.'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'adminpassword'
        username = 'admin'
        
        user = None
        # There might be a user with the email or the username, but not both.
        # This can happen if data was created in a way that bypassed the model's clean methods.
        try:
            user = User.objects.get(Q(username=username) | Q(email=email))
            self.stdout.write(self.style.WARNING(f'Found existing user with username "{user.username}" or email "{user.email}". Consolidating to admin account.'))
        except User.DoesNotExist:
            # If no user exists with either, create a new one.
            User.objects.create_user(username=username, email=email, password=password)
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'No conflicting user found. Created new admin user.'))
        except User.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR('Multiple users found with the same admin credentials. Please resolve this manually in the database.'))
            return

        # Consolidate and update the user to be a superuser
        user.username = username
        user.email = email
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" is configured correctly. You can now log in with email "{email}".'))


