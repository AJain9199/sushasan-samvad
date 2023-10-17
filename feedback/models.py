import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _
import moviepy.editor as mp
import speech_recognition as sr


def get_transcript(filepath, recording_name):
    vid = mp.VideoFileClip(filepath)
    vid.audio.write_audiofile(f"{recording_name}_audio.wav")
    r = sr.Recognizer()
    with sr.AudioFile(f"{recording_name}_audio.wav") as source:
        data = r.record(source)
        text = r.recognize_google(data, language="hi-In")
    return text.encode('utf-8')


class State(models.Model):
    name = models.CharField(_('State name'), max_length=200)

    def __str__(self):
        return self.name


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(_('District name'), max_length=200)

    def __str__(self):
        return self.name


class Village(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
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
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    village = models.ForeignKey(Village, on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)

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
    date = models.DateField(default=datetime.datetime.now().date())
    made_by = models.ForeignKey(User, on_delete=models.CASCADE)
    important = models.BooleanField(default=False)


class ScheduleMeeting(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    date = models.DateField()
