from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    fieldsets = [[None, {'fields': (
        'username',
        'password',
        'is_active',
        'is_superuser',
        'is_staff',
        'groups'
    )}]]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
