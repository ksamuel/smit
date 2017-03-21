
from django.db.utils import OperationalError
from django.apps import AppConfig


class WebsiteConfig(AppConfig):

    name = 'website'

    def ready(self):

        try:
            from django.contrib.auth.models import Group

            from .models import CustomUser

            groups = []
            for group in ('helicopter_pilot', 'operator'):
                try:
                    groups.append(Group.objects.get(name=group))
                except Group.DoesNotExist:
                    groups.append(Group.objects.create(name=group))

            try:
                CustomUser.objects.get(username="admin")
            except CustomUser.DoesNotExist:
                admin = CustomUser.objects.create(
                    username="admin",
                    is_superuser=True,
                )
                admin.set_password('admin')
                admin.save()
                for group in groups:
                    admin.groups.add(group)
        except OperationalError:
            pass
