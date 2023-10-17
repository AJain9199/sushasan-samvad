from django.urls import path, include
from . import views

urlpatterns = [
    path('register/', views.register, name="register"),
    path('upload_meeting/', views.upload_meeting),
    path('meetings/<int:meeting_id>', views.meeting, name='meeting'),
    path('district/<int:dist_id>', views.district, name='district'),
    path('village/<int:village_id>', views.village, name='village'),
    path('share-grievance/', views.share_grievance, name='share_grievance'),
    path('mark-important/', views.mark_as_important, name='mark_imp'),
    path('mark-unimportant/', views.mark_as_unimportant, name='mark_unimp'),
    path('agendas/', views.agendas, name='agendas'),
    path('schedule-meeting/', views.schedule_meeting, name='schedule_meeting'),
    path('', views.index, name='index'),
    path('scheduled-meetings/', views.scheduled_meeting, name='scheduled_meeting'),
    path('community/', views.community, name='community'),
    path('login/', views.login_view, name='login')
]
