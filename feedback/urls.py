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
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('aadhaar_data/', views.decode_aadhaar_qr, name='aadhaar_data'),
    path('create_shg/', views.create_shg, name='create_shg'),
    path('shgs/', views.shgs, name='shgs'),
    path('shg/<int:shg_id>', views.shg, name='shg'),
    path('shg/<int:shg_id>/members', views.shg_members, name='shg_members'),
    path('shg/update_role', views.update_role, name='update_role'),
    path('shg/join', views.join_shg, name='join_shg'),
]
