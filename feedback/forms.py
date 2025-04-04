import random

from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Form
from .models import User, Meeting, MeetingSuggestion, Grievance, ScheduleMeeting, SelfHelpGroup
from django import forms
from django.utils.translation import gettext as _
from django.contrib.auth.models import Group
from django.urls import reverse


class RegistrationForm(ModelForm):
    role = forms.ChoiceField(choices=(
        (2, _("Villager")),
        (1, _("Village Administrator")),
        (3, _("District Administrator"))
    ))

    def save(self, commit=True):
        user = super().save()

        Group.objects.get(id=self.cleaned_data['role']).user_set.add(user)
        return user

    class Meta:
        model = User
        fields = ('name', 'state', 'district', 'sub_district', 'village', 'department')


class UploadMeetingForm(ModelForm):
    date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Meeting
        fields = ('date', 'recording')


class SuggestionForm(ModelForm):
    class Meta:
        model = MeetingSuggestion
        fields = ('audio',)


class ShareGrievanceForm(ModelForm):
    class Meta:
        model = Grievance
        fields = ('audio',)


class ScheduleMeetingForm(ModelForm):
    date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = ScheduleMeeting
        fields = ('date',)


class LoginForm(Form):
    user_code = forms.IntegerField()


class SHGForm(ModelForm):
    startup_amount = forms.IntegerField(label=_("Startup Amount (Your Contribution)"))

    def __init__(self, *args, **kwargs):
        if kwargs.get('request'):
            self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit = ...):
        shg = super().save(commit=False)
        shg.created_by = self.request.user
        shg.members.add(self.request.user, through_defaults={'amount': self.cleaned_data['startup_amount']})
        shg.pool = self.cleaned_data['startup_amount']
        if commit:
            shg.save()
        return shg

    class Meta:
        model = SelfHelpGroup
        fields = ('name', 'min_contribution', 'description')
