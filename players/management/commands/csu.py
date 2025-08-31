from django.core.management import BaseCommand

from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(
            username="admin",
            email='admin@test.com',
            is_active=True,
            is_superuser=True,
            is_staff=True

        )
        user.set_password('12345')
        user.save()