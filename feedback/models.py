import django.utils.timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from smart_selects.db_fields import ChainedForeignKey
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.serializers.json import DjangoJSONEncoder


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
    class SHGRoles(models.IntegerChoices):
        ADMIN = 1, _("Administrator")
        MEMBER = 2, _("Member")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    shg = models.ForeignKey('SelfHelpGroup', on_delete=models.CASCADE)
    role = models.IntegerField(choices=SHGRoles.choices, default=SHGRoles.MEMBER)

    contrib = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)

    @property
    def amount(self):
        a = 0
        for [_, amt] in self.contrib:
            a += amt
        return a

    def contribute(self, amount):
        self.contrib.append((django.utils.timezone.now(), amount))
        self.save()

    class Meta:
        unique_together = ('user', 'shg')


class GenericLoan(models.Model):
    class RepaymentFrequency(models.IntegerChoices):
        BIWEEKLY = 0, _("Biweekly")
        WEEKLY = 1, _("Weekly")
        MONTHLY = 2, _("Monthly")
        QUARTERLY = 3, _("Quarterly")

    class Status(models.IntegerChoices):
        PENDING = 0, _("Pending")
        ACTIVE = 1, _("Approved")
        REJECTED = 2, _("Rejected")
        COMPLETED = 3, _("Completed")
        DEFAULTED = 4, _("Defaulted")

    principal = models.FloatField(_("Principal"))
    date = models.DateField(default=django.utils.timezone.now)
    purpose = models.TextField(_("Purpose"))
    approval_date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(_("Duration (in months)"))
    repayment_freq = models.IntegerField(_("Repayment Frequency"), choices=RepaymentFrequency.choices,
                                         default=RepaymentFrequency.MONTHLY)
    interest_rate = models.FloatField(_("Annual Interest Rate"))

    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)

    total_payable = models.FloatField(_("Total Payable"), default=0)
    amortization_schedule = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)

    def approve(self):
        add_amortzn_dates(self.amortization_schedule, self.repayment_freq, django.utils.timezone.now())
        self.status = self.Status.ACTIVE
        self.approval_date = django.utils.timezone.now()
        self.save()

    @property
    def amount_paid(self):
        if self.status != self.Status.ACTIVE:
            return 0
        p = 0
        for installment in self.amortization_schedule:
            if datetime.fromisoformat(installment[3]) < django.utils.timezone.now():
                p += installment[2]
        return p

    @property
    def remaining_balance(self):
        return self.total_payable - self.amount_paid

    @property
    def interest(self):
        return self.total_payable - self.principal

    @property
    def is_approved(self):
        return self.status == self.Status.ACTIVE

    class Meta:
        abstract = True


class SHGLoan(GenericLoan):
    REDUCING_FACTOR = 0.55

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shg = models.ForeignKey('SelfHelpGroup', on_delete=models.CASCADE)

    def save(
        self,
        force_insert = ...,
        force_update = ...,
        using = ...,
        update_fields = ...,
    ):
        if not self.amortization_schedule:
            self.total_payable, self.amortization_schedule = calculate_repayment_terms(
                self.shg.interest_model,
                self.principal,
                self.duration,
                self.interest_rate,
                self.repayment_freq
            )
        super().save()

    @property
    def percent_of_pool(self):
        return round((self.principal/self.shg.pool) * 100, 1)

    @property
    def get_amortization(self):
        amort = []
        if self.status != self.Status.ACTIVE:
            return [(sched, False) for sched in self.amortization_schedule]
        for sched in self.amortization_schedule:
            if django.utils.timezone.now() >= datetime.fromisoformat(sched[3]):
                amort.append((sched, True))
            else:
                amort.append((sched, False))
        return amort


def calculate_params(duration, interest_rate, repayment_freq):
    # Calculate the number of installments and the period interest rate

    installment_count = duration  # in months
    interest_rate = (interest_rate / 100)  # annual interest rate

    period_interest_rate = 0

    if repayment_freq == SHGLoan.RepaymentFrequency.MONTHLY:
        period_interest_rate = interest_rate / 12
    if repayment_freq == SHGLoan.RepaymentFrequency.WEEKLY:
        installment_count *= 4
        period_interest_rate = interest_rate / 52
    elif repayment_freq == SHGLoan.RepaymentFrequency.BIWEEKLY:
        installment_count *= 2
        period_interest_rate = interest_rate / 26
    elif repayment_freq == SHGLoan.RepaymentFrequency.QUARTERLY:
        installment_count //= 3
        period_interest_rate = interest_rate / 4

    installment_count = max(1, installment_count)
    return installment_count, period_interest_rate

def get_next_payment_date(current_date, freq):
    if freq == SHGLoan.RepaymentFrequency.WEEKLY:
        return current_date + timedelta(days=7)
    elif freq == SHGLoan.RepaymentFrequency.BIWEEKLY:
        return current_date + timedelta(days=14)
    elif freq == SHGLoan.RepaymentFrequency.MONTHLY:
        return current_date + relativedelta(months=1)
    elif freq == SHGLoan.RepaymentFrequency.QUARTERLY:
        return current_date + relativedelta(months=3)


def add_amortzn_dates(sched, freq, start_date):
    next_date = 0
    payment_date = get_next_payment_date(start_date, freq)
    for installment in sched:
        installment.append(payment_date)
        payment_date = get_next_payment_date(payment_date, freq)
    return sched
        

def calculate_repayment_terms(interest_model, principal, duration, interest_rate, repayment_freq):
    amortization_schedule = []
    total_payable = 0

    shg_int_model = interest_model

    ins_count, prd_rate = calculate_params(duration, interest_rate, repayment_freq)

    if shg_int_model == SelfHelpGroup.InterestModel.FLAT:
        total_interest = principal * prd_rate * ins_count
        total_payable = principal + total_interest

        total_installment = total_payable / ins_count
        principal_installment = principal / ins_count
        interest_installment = total_interest / ins_count

        amortization_schedule = [[
                                    round(principal_installment, 2),
                                    round(interest_installment, 2),
                                    round(total_installment, 2),
                                ]] * ins_count

    elif shg_int_model == SelfHelpGroup.InterestModel.DECLINING:
        remaining_principal = principal
        total_payable = principal

        principal_per_installment = principal / ins_count

        for i in range(ins_count):
            interest_payment = remaining_principal * prd_rate
            principal_payment = principal_per_installment
            installment_amount = principal_payment + interest_payment

            total_payable += interest_payment
            remaining_principal -= principal_payment

            amortization_schedule.append([
                round(principal_payment, 2), round(2, interest_payment), round(2, installment_amount)])
    elif shg_int_model == SelfHelpGroup.InterestModel.FLAT_DECLINING:
        total_interest = principal * prd_rate * ins_count * SHGLoan.REDUCING_FACTOR
        total_payable = principal + total_interest
        total_installment = total_payable / ins_count
        principal_installment = principal / ins_count
        interest_installment = total_interest / ins_count

        amortization_schedule = [
                                    round(principal_installment, 2),
                                    round(interest_installment, 2),
                                    round(total_installment, 2),
                                ] * ins_count
    elif shg_int_model == SelfHelpGroup.InterestModel.EMI or shg_int_model == SelfHelpGroup.InterestModel.COMPOUND:
        if prd_rate > 0:
            emi = principal * (prd_rate * (1 + prd_rate) ** ins_count) / ((1 + prd_rate) ** ins_count - 1)
            total_installment = principal * emi
        else:
            total_installment = principal / ins_count

        remaining = principal
        for i in range(ins_count):
            interest_installment = remaining * prd_rate
            principal_installment = total_installment - interest_installment

            if i == ins_count - 1:
                principal_installment = remaining
                total_installment = principal_installment + interest_installment

            if remaining < 0.01:
                remaining = 0

            amortization_schedule.append([
                round(principal_installment, 2), round(interest_installment, 2), round(total_installment, 2)])
    return total_payable, amortization_schedule


class SelfHelpGroup(models.Model):
    class InterestModel(models.IntegerChoices):
        FLAT = 0, _("Flat Rate")
        DECLINING = 1, _("Declining Balance")
        FLAT_DECLINING = 2, _("Reducing Flat Rate")
        EMI = 3, _("EMI")
        COMPOUND = 4, _("Compound")

    name = models.CharField(_('SHG name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    target = models.CharField(_('Target members'), max_length=200, blank=True)
    members = models.ManyToManyField(User, blank=True, through="SHGContribution", related_name='members')
    min_contribution = models.IntegerField(_("Minimum Contribution for new users"), default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='founder')

    interest_model = models.IntegerField(choices=InterestModel.choices, default=InterestModel.FLAT)

    @property
    def pool(self):
        p = 0
        for contri in self.shgcontribution_set.all():
            p += contri.amount
        
        for loan in SHGLoan.objects.filter(shg_id=self.id):
            if loan.status == GenericLoan.Status.ACTIVE:
                p -= loan.principal
                p += loan.amount_paid

        for linkage in self.linkageapplication_set.all():
            if linkage.status == GenericLoan.Status.ACTIVE:
                p += linkage.principal
                p -= linkage.amount_paid

        return p

    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    date = models.DateField(default=django.utils.timezone.now)


class ExternalLinkageBank(models.Model):
    name = models.CharField(_('Bank name'), max_length=200)
    bookkeeping_requirement = models.DurationField(_("Bookkeeping Requirement for Applicant SHGs"), default=timedelta(days=180))
    member_requirement = models.IntegerField(_("Minimum Number of Members"), default=5)
    pool_requirement = models.IntegerField(_("Minimum Pool"), default=0)
    avg_interest_rate = models.FloatField(_("Average Interest Rate"))
    min_loan = models.IntegerField(_("Minimum Loan Amount"), default=0)
    review_time = models.DurationField(_("Typical Review Time"), default=timedelta(days=30))

    applications = models.ManyToManyField(SelfHelpGroup, blank=True, related_name='applications', through='LinkageApplication')
    image = models.ImageField(upload_to='bank_images', blank=True, null=True)

    def __str__(self):
        return self.name


class LinkageApplication(GenericLoan):
    shg = models.ForeignKey(SelfHelpGroup, on_delete=models.CASCADE)
    bank = models.ForeignKey(ExternalLinkageBank, on_delete=models.CASCADE)

    def save(
        self,
        force_insert = ...,
        force_update = ...,
        using = ...,
        update_fields = ...,
    ):
        if not self.amortization_schedule:
            self.total_payable, self.amortization_schedule = calculate_repayment_terms(
                SelfHelpGroup.InterestModel.EMI,
                self.principal,
                self.duration,
                self.interest_rate,
                self.repayment_freq
            )
        super().save()

