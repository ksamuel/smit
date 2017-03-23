from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser, Settings


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


class SettingsAdmin(admin.ModelAdmin):
    model = Settings
    list_display = ['name', 'active']


admin.site.register(Settings, SettingsAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)

