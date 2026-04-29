from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create default admin user"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = "dancan.mbuvi"
        password = "adm:/2025"

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email="dancanmutuku7@gmail.com",
                password=password,
            )
            self.stdout.write(self.style.SUCCESS("Admin created successfully"))
        else:
            self.stdout.write("Admin already exists")
