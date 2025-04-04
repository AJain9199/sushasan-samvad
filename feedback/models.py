import datetime

import django.utils.timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from smart_selects.db_fields import ChainedForeignKey


class State(models.Model):
    name = models.CharField(_('State name'), max_length=200)

    def __str__(self):
        return self.name


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(_('District name'), max_length=200)

    def __str__(self):
        return self.name


class SubDistrict(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField(_("Sub-District name"), max_length=200)

    def __str__(self):
        return self.name


class Village(models.Model):
    sub_district = models.ForeignKey(SubDistrict, on_delete=models.CASCADE)
    name = models.CharField(_('Village name'), max_length=200)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(_('District name'), max_length=200)

    def __str__(self):
        return self.name


class User(AbstractUser):
    name = models.CharField(_('Your name'), max_length=200, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    district = ChainedForeignKey(District,
                                 chained_field="state",
                                 chained_model_field="state",
                                 show_all=False,
                                 auto_choose=True,
                                 sort=True,
                                 on_delete=models.CASCADE
                                 )

    sub_district = ChainedForeignKey(SubDistrict,
                                     chained_field="district",
                                     chained_model_field="district",
                                     show_all=False,
                                     auto_choose=True,
                                     sort=True,
                                     on_delete=models.CASCADE
                                     )

    village = ChainedForeignKey(
        Village,
        chained_field="sub_district",
        chained_model_field="sub_district",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE, blank=True, null=True
    )

    otp = models.IntegerField(null=True, blank=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)
    user_code = models.BigIntegerField(null=True, blank=True)

    first_name = None
    last_name = None
    username = None

    USERNAME_FIELD = 'name'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save()
        self.set_unusable_password()


def validate_video(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.mp4', '.mov']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def validate_audio(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.mp3', '.wav', '.webm']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


class Meeting(models.Model):
    date = models.DateField(_("Meeting date"))
    recording = models.FileField(_("Meeting recording"), upload_to="meetings", validators=[validate_video])
    village = models.ForeignKey(Village, on_delete=models.CASCADE)


class MeetingSuggestion(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    audio = models.FileField(_("Meeting suggestion"), upload_to="suggestions", validators=[validate_audio])
    made_by = models.ForeignKey(User, on_delete=models.CASCADE)


class Grievance(models.Model):
    audio = models.FileField(_("Grievance"), upload_to="grievances", validators=[validate_audio])
    date = models.DateField(default=django.utils.timezone.now)
    made_by = models.ForeignKey(User, on_delete=models.CASCADE)
    important = models.BooleanField(default=False)


class ScheduleMeeting(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    date = models.DateField()


class SHGContribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(_("Amount"))
    date = models.DateField(default=django.utils.timezone.now)
    shg = models.ForeignKey('SelfHelpGroup', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'shg')


class SelfHelpGroup(models.Model):
    name = models.CharField(_('SHG name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    target = models.CharField(_('Target members'), max_length=200, blank=True)
    members = models.ManyToManyField(User, blank=True, through="SHGContribution", related_name='members')
    pool = models.IntegerField(default=0)
    min_contribution = models.IntegerField(_("Minimum Contribution for new users"), default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='founder')


    def __str__(self):
        return self.name
