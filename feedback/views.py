import random
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from .forms import RegistrationForm, UploadMeetingForm, SuggestionForm, ShareGrievanceForm, ScheduleMeetingForm, LoginForm, SHGForm
from .models import Meeting, MeetingSuggestion, State, District, SubDistrict, Village, Grievance, ScheduleMeeting, User, \
    SelfHelpGroup
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib import messages
from pyaadhaar import utils


VILLAGER = 2
VILLAGE_ADMIN = 1
DISTRICT_ADMIN = 3


user_codes = [i for i in range(0, 99999)]


def is_role(user, role):
    return user.groups.filter(id=role).exists()


def is_district_admin(user):
    return is_role(user, DISTRICT_ADMIN)


def is_village_admin(user):
    return is_role(user, VILLAGE_ADMIN)


def decode_aadhaar_qr(request):
    if request.method == 'POST':
        print(request.POST['aadhaar'])
        aadhaar_data = utils.AadhaarQrAuto(request.POST['aadhaar']).decodeddata()
        print(aadhaar_data)
        state_id = State.objects.get(name__icontains=aadhaar_data['state']).pk
        district_id = subdistict_id = village_id = None
        if state_id and aadhaar_data.get('dist'):
            district_id = District.objects.get(name__icontains=aadhaar_data['dist'], state_id=state_id).pk

        if district_id and aadhaar_data.get('subdist'):
            subdistict_id = SubDistrict.objects.get(name__icontains=aadhaar_data['subdist'], district_id=district_id).pk

        if village_id and aadhaar_data.get('vtc'):
            village_id = Village.objects.get(name__icontains=aadhaar_data['vtc'], sub_district_id=subdistict_id).pk

        return JsonResponse({'name': aadhaar_data['name'], 'state': state_id, 'district': district_id, 'sub_district': subdistict_id, 'village': village_id})


def register(request):
    # print(settings.SMS_CLIENT.publish(PhoneNumber="+917717479808", Message="OTP IS TESTING. IGNORE."))
    if request.method == 'GET':
        form = RegistrationForm()
        return render(request, 'register.html', {'form': form})
    elif request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.errors:
            return render(request, 'register.html', {'form': form})
        user = form.save()

        idx = random.randint(0, len(user_codes))
        user.user_code = user_codes[idx]
        user_codes.pop(idx)
        user.save()

        messages.success(request, f"Your user code is {user.user_code}. Please remember it for logging in later.")

        user.save()
        login(request, user)
        if is_role(user, DISTRICT_ADMIN):
            return HttpResponseRedirect(reverse('district', args=[user.district_id]))
        else:
            return HttpResponseRedirect(reverse('village', args=[user.village_id]))


def community(request):
    return render(request, "community.html")


def upload_meeting(request):
    if request.method == 'GET':
        form = UploadMeetingForm()
        return render(request, 'upload_meeting.html', {'form': form})
    elif request.method == 'POST':
        form = UploadMeetingForm(request.POST, request.FILES)
        meeting = form.save(commit=False)
        meeting.village = request.user.village
        meeting.save()
        if not form.is_valid():
            return render(request, 'upload_meeting.html', {'form': form})
        return HttpResponseRedirect(reverse('meeting', args=(meeting.id, )))


@csrf_exempt
def meeting(request, meeting_id):
    if request.method == 'GET':
        m = Meeting.objects.get(id=meeting_id)
        print(is_role(request.user, VILLAGE_ADMIN))
        if is_role(request.user, VILLAGE_ADMIN) or is_role(request.user, DISTRICT_ADMIN):
            return render(request, 'meeting.html',
                          {'meeting': m, 'suggestions': MeetingSuggestion.objects.filter(meeting_id=m.pk)})
        else:
            form = SuggestionForm()
            return render(request, 'meeting.html', {'meeting': m, 'form': form})
    elif request.method == 'POST':
        form = SuggestionForm(request.POST, request.FILES)
        suggestion = form.save(commit=False)
        suggestion.meeting = Meeting.objects.get(id=meeting_id)
        suggestion.made_by = request.user
        suggestion.save()
        return JsonResponse({"url": reverse('village', args=(request.user.village.id,))})


@user_passes_test(is_district_admin)
def district(request, dist_id):
    dist = District.objects.get(id=dist_id)
    return render(request, 'district.html', {'district': dist, 'villages': Village.objects.filter(district_id=dist_id)})


def village(request, village_id):
    meetings = Meeting.objects.filter(village_id=village_id)
    grievances = Grievance.objects.filter(made_by__village_id=village_id)
    return render(request, 'village.html', {'meetings': meetings, 'village': Village.objects.get(id=village_id), 'grievances': grievances, 'num_meetings': len(ScheduleMeeting.objects.filter(village=request.user.village))})

@csrf_exempt
def share_grievance(request):
    if request.method == 'GET':
        form = ShareGrievanceForm()
        return render(request, 'upload grievance.html', {'form': form})
    elif request.method == 'POST':
        form = ShareGrievanceForm(request.POST, request.FILES)
        grievance = form.save(commit=False)
        grievance.made_by = request.user
        grievance.save()
        return JsonResponse({'url': reverse('village', args=(request.user.village_id, ))})


@csrf_exempt
def mark_as_important(request):
    if request.method == 'POST':
        g = Grievance.objects.get(id=request.POST['id'])
        g.important = True
        g.save()
        return HttpResponse('Grievance marked as important')


@csrf_exempt
def mark_as_unimportant(request):
    if request.method == 'POST':
        g = Grievance.objects.get(id=request.POST['id'])
        g.important = False
        g.save()
        return HttpResponse('Grievance marked as unimportant')


def agendas(request):
    return render(request, 'agendas.html', {'grievances': Grievance.objects.filter(made_by__village_id=request.user.village.id, important=True), 'village': Village.objects.get(id=request.user.village.id)})


def schedule_meeting(request):
    if request.method == 'GET':
        form = ScheduleMeetingForm()
        return render(request, 'schedule_meeting.html', {'form': form})
    elif request.method == 'POST':
        form = ScheduleMeetingForm(request.POST)
        scheduled_meeting = form.save(commit=False)
        scheduled_meeting.village = request.user.village
        scheduled_meeting.save()

        return HttpResponseRedirect(reverse('village', args=(request.user.village.id, )))


def index(request):
    return render(request, "index.html")


@csrf_exempt
def scheduled_meeting(request):
    if request.method == 'POST':
        print(request.POST)
        scheduled_meetings = ScheduleMeeting.objects.filter(village=request.POST['id'])
        meets = {}
        for meeting in scheduled_meetings:
            meets[meeting.id] = f"{meeting.date.day}/{meeting.date.month}/{meeting.date.year}"

        return JsonResponse(meets)


def login_view(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, "login.html", {"form": form})
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        usr = User.objects.get(user_code=form['user_code'].value())
        login(request, usr)
        return HttpResponseRedirect(reverse('village', args=(request.user.village.id, )))


@login_required()
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


@login_required()
def create_shg(request):
    if request.method == 'GET':
        form = SHGForm()
        return render(request, 'create_shg.html', {'form': form})
    elif request.method == 'POST':
        form = SHGForm(request.POST, request=request)
        shg = form.save()
        return HttpResponseRedirect(reverse('village', args=(request.user.village.id,)))


def shgs(request):
    shg_set = SelfHelpGroup.objects.all()


    if request.GET.get('dist_search'):
        shg_set = shg_set.filter(created_by__district=request.user.district)
    else:
        shg_set = shg_set.filter(created_by__village=request.user.village)

    return render(request, 'shgs.html', {'shgs': shg_set})
