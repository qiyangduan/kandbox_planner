from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            for user in settings.ADMINS:
                username = user[0].replace(' ', '')
                email = user[1]
                password =  settings.ADMIN_PASSWORD
                admin = User.objects.create_user(email=email, username=username, password=password)
                admin.is_active = True
                admin.is_admin = True
                admin.is_staff = True
                admin.is_superuser = True

                admin.save()
                print('Created super user: %s (%s) with password from setting.ADMIN_PASSWORD' % (username, email))
        else:
            print('Users DB is not empty, and no superuser created.')
