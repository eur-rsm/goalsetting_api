from django.contrib import admin

from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'sub_id', 'onesignal_id']


admin.site.register(Profile, ProfileAdmin)
