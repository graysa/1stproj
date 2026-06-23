from django.contrib import admin
from django.contrib.admin import AdminSite
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
from .models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


# Add "Analytics Dashboard" link to admin index
AdminSite.index_template = None  # use default

original_each_context = AdminSite.each_context
def patched_each_context(self, request, **kwargs):
    ctx = original_each_context(self, request, **kwargs)
    ctx['dashboard_url'] = reverse('admin_dashboard')
    return ctx
AdminSite.each_context = patched_each_context


class CareGroupAdminForm(forms.ModelForm):
    new_pin = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text='Leave blank to keep the existing PIN. Enter a value to set a new one.',
    )

    class Meta:
        model = CareGroup
        fields = ['name', 'meeting_day', 'meeting_time', 'new_pin']

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_pin = self.cleaned_data.get('new_pin')
        if raw_pin:
            instance.pin = make_password(raw_pin)
        if commit:
            instance.save()
        return instance


class MemberInline(admin.TabularInline):
    model = Member
    extra = 1
    fields = ['name', 'is_active']


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ['member', 'is_present']


class VisitorInline(admin.TabularInline):
    model = Visitor
    extra = 0
    fields = ['name', 'note']


@admin.register(CareGroup)
class CareGroupAdmin(admin.ModelAdmin):
    form = CareGroupAdminForm
    list_display = ['name', 'get_meeting_day_display', 'meeting_time']
    inlines = [MemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'is_active']
    list_filter = ['group', 'is_active']


@admin.register(MeetingDate)
class MeetingDateAdmin(admin.ModelAdmin):
    list_display = ['group', 'date', 'attendance_count']
    list_filter = ['group']
    date_hierarchy = 'date'
    inlines = [AttendanceRecordInline, VisitorInline]

    def attendance_count(self, obj):
        return obj.attendance_count()
    attendance_count.short_description = 'Present'


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'meeting_date', 'note']
    list_filter = ['meeting_date__group']
