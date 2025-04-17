from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from feedback.models import User, SelfHelpGroup, ExternalLinkageBank, LinkageApplication


class CustomUserAdmin(UserAdmin):
    list_display = ('name', 'state', 'district', 'sub_district', 'village', 'department')
    list_filter = ('is_staff',)
    ordering = ('name',)


def approve_application(modeladmin, request, queryset):
    for q in queryset:
        q.approve()


class LinkageApplicationAdmin(admin.ModelAdmin):
    list_display = ('shg', 'bank', 'status')
    actions = [approve_application]

# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(SelfHelpGroup)
admin.site.register(ExternalLinkageBank)
admin.site.register(LinkageApplication, LinkageApplicationAdmin)