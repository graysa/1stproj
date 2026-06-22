from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list, meeting_detail, add_visitor
from attendance.views.analytics import (
    analytics, analytics_data, admin_dashboard, admin_dashboard_data
)

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    path('meetings/<str:date>/', meeting_detail, name='meeting_detail'),
    path('meetings/<str:date>/visitor/', add_visitor, name='add_visitor'),
    path('analytics/', analytics, name='analytics'),
    path('analytics/data/', analytics_data, name='analytics_data'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/data/', admin_dashboard_data, name='admin_dashboard_data'),
]
