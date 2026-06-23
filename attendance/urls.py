from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import (
    meeting_list, add_meeting_date, meeting_detail, add_visitor,
    delete_meeting, members_list, add_member, toggle_member, change_pin,
)
from attendance.views.analytics import (
    analytics, analytics_data, admin_dashboard, admin_dashboard_data, export_csv
)

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    path('meetings/new/', add_meeting_date, name='add_meeting_date'),
    path('meetings/<str:date>/', meeting_detail, name='meeting_detail'),
    path('meetings/<str:date>/visitor/', add_visitor, name='add_visitor'),
    path('meetings/<str:date>/delete/', delete_meeting, name='delete_meeting'),
    path('members/', members_list, name='members_list'),
    path('members/add/', add_member, name='add_member'),
    path('members/<int:member_id>/toggle/', toggle_member, name='toggle_member'),
    path('settings/pin/', change_pin, name='change_pin'),
    path('analytics/', analytics, name='analytics'),
    path('analytics/data/', analytics_data, name='analytics_data'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/data/', admin_dashboard_data, name='admin_dashboard_data'),
    path('admin-dashboard/export/', export_csv, name='export_csv'),
]
