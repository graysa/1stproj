from django.urls import path
from django.http import HttpResponse
from attendance.views.auth import login_view, logout_view


def _placeholder(request):
    return HttpResponse('coming soon')


urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # Stub for Task 4 — replaced when meeting list view is implemented
    path('meetings/', _placeholder, name='meeting_list'),
]
