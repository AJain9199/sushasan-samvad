import random

from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Form
from .models import User, Meeting, MeetingSuggestion, Grievance, ScheduleMeeting, SelfHelpGroup, SHGContribution, SHGLoan
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

        shg.save()
        membership = SHGContribution(user=self.request.user, shg=shg, role=SHGContribution.SHGRoles.ADMIN)
        membership.contribute(self.cleaned_data['startup_amount'])
        if commit:
            shg.save()
            membership.save()
        return shg

    class Meta:
        model = SelfHelpGroup
        fields = ('name', 'startup_amount', 'min_contribution', 'target', 'description')


class SHGLoanRequestForm(ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs.get('request'):
            self.request = kwargs.pop('request')

        if kwargs.get('shg_id'):
            self.shg = kwargs.pop('shg_id')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        shg_loan_request = super().save(commit=False)
        shg_loan_request.user = self.request.user
        if commit:
            shg_loan_request.save()
        return shg_loan_request

    class Meta:
        model = SHGLoan
        fields = ('principal', 'purpose', 'duration', 'repayment_freq', 'interest_rate')