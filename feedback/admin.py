from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from feedback.models import User, SelfHelpGroup, ExternalLinkageBank


class CustomUserAdmin(UserAdmin):
    list_display = ('name', 'state', 'district', 'sub_district', 'village', 'department')
    list_filter = ('is_staff',)
    ordering = ('name',)

# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(SelfHelpGroup)
admin.site.register(ExternalLinkageBank)