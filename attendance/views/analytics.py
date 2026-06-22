import datetime
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from attendance.decorators import group_login_required, staff_required
from attendance.models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


def _default_date_range():
    today = datetime.date.today()
    return today - datetime.timedelta(days=91), today


def _parse_date_params(request):
    try:
        from_date = datetime.date.fromisoformat(request.GET.get('from', ''))
    except ValueError:
        from_date = None
    try:
        to_date = datetime.date.fromisoformat(request.GET.get('to', ''))
    except ValueError:
        to_date = None
    if not from_date or not to_date:
        from_date, to_date = _default_date_range()
    return from_date, to_date


@group_login_required
def analytics(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    return render(request, 'attendance/analytics.html', {'group': group})


@group_login_required
def analytics_data(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    from_date, to_date = _parse_date_params(request)

    meetings = MeetingDate.objects.filter(
        group=group, date__gte=from_date, date__lte=to_date
    ).order_by('date')
    meeting_ids = list(meetings.values_list('pk', flat=True))
    meeting_count = len(meeting_ids)

    weekly_labels, weekly_totals = [], []
    for meeting in meetings:
        present = AttendanceRecord.objects.filter(
            meeting_date=meeting, is_present=True
        ).count()
        visitors = Visitor.objects.filter(meeting_date=meeting).count()
        weekly_labels.append(str(meeting.date))
        weekly_totals.append(present + visitors)

    active_members = Member.objects.filter(group=group, is_active=True)
    member_rates = []
    for member in active_members:
        attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, member=member, is_present=True
        ).count()
        rate = round((attended / meeting_count) * 100, 1) if meeting_count > 0 else 0.0
        member_rates.append({
            'name': member.name,
            'rate': rate,
            'attended': attended,
            'total': meeting_count,
        })

    return JsonResponse({
        'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
        'member_rates': member_rates,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })


@staff_required
def admin_dashboard(request):
    groups = CareGroup.objects.all().order_by('name')
    return render(request, 'attendance/admin_dashboard.html', {'groups': groups})


@staff_required
def admin_dashboard_data(request):
    from_date, to_date = _parse_date_params(request)
    groups = CareGroup.objects.all().order_by('name')
    result = []

    for group in groups:
        meetings = MeetingDate.objects.filter(
            group=group, date__gte=from_date, date__lte=to_date
        ).order_by('date')
        meeting_ids = list(meetings.values_list('pk', flat=True))
        meeting_count = len(meeting_ids)

        weekly_labels, weekly_totals = [], []
        for meeting in meetings:
            present = AttendanceRecord.objects.filter(
                meeting_date=meeting, is_present=True
            ).count()
            visitors = Visitor.objects.filter(meeting_date=meeting).count()
            weekly_labels.append(str(meeting.date))
            weekly_totals.append(present + visitors)

        active_member_count = Member.objects.filter(group=group, is_active=True).count()
        total_attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, is_present=True
        ).count()
        denominator = meeting_count * active_member_count
        overall_rate = round((total_attended / denominator) * 100, 1) if denominator > 0 else 0.0

        result.append({
            'name': group.name,
            'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
            'overall_rate': overall_rate,
            'meeting_count': meeting_count,
        })

    return JsonResponse({
        'groups': result,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })
