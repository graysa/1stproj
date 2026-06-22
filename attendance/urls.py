from django.urls import path
from django.http import HttpResponse
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list


def _placeholder(request, *args, **kwargs):
    return HttpResponse('coming soon')


urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    # Stub for Task 5 — replaced when meeting detail view is implemented
    path('meetings/<str:date>/', _placeholder, name='meeting_detail'),
]
