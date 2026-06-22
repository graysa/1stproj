import datetime as dt
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from attendance.decorators import group_login_required
from attendance.models import CareGroup, MeetingDate, Member, AttendanceRecord, Visitor
import attendance.forms as attendance_forms


@group_login_required
def meeting_list(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    meetings = MeetingDate.objects.filter(group=group).order_by('-date')

    total = meetings.count()
    avg_attendance = 0
    if total:
        total_present = sum(m.attendance_count() for m in meetings)
        avg_attendance = round(total_present / total, 1)

    return render(request, 'attendance/meeting_list.html', {
        'group': group,
        'meetings': meetings,
        'total_meetings': total,
        'avg_attendance': avg_attendance,
        'active_member_count': Member.objects.filter(group=group, is_active=True).count(),
    })


@group_login_required
def add_meeting_date(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    if request.method == 'POST':
        date_str = request.POST.get('date', '')
        try:
            date = dt.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return redirect('meeting_list')
        MeetingDate.objects.get_or_create(group=group, date=date)
        return redirect('meeting_detail', date=date.isoformat())
    today = dt.date.today().isoformat()
    return render(request, 'attendance/add_meeting_date.html', {
        'group': group,
        'today': today,
    })


@group_login_required
def meeting_detail(request, date):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise Http404

    meeting = get_object_or_404(MeetingDate, group=group, date=parsed_date)
    active_members = Member.objects.filter(group=group, is_active=True)
    existing = {r.member_id: r for r in AttendanceRecord.objects.filter(meeting_date=meeting)}

    if request.method == 'POST' and request.POST.get('action') == 'save_attendance':
        present_ids = set()
        for pk in request.POST.getlist('present_members'):
            try:
                present_ids.add(int(pk))
            except (ValueError, TypeError):
                pass
        for member in active_members:
            AttendanceRecord.objects.update_or_create(
                meeting_date=meeting,
                member=member,
                defaults={'is_present': member.pk in present_ids},
            )
        return redirect('meeting_list')

    # Calculate 90-day attendance rate per member
    ninety_days_ago = parsed_date - dt.timedelta(days=90)
    recent_meetings = MeetingDate.objects.filter(group=group, date__gte=ninety_days_ago, date__lte=parsed_date)
    meeting_count = recent_meetings.count()

    member_data = []
    for m in active_members:
        is_present = existing[m.pk].is_present if m.pk in existing else False
        rate = 0.0
        if meeting_count:
            attended = AttendanceRecord.objects.filter(
                meeting_date__in=recent_meetings, member=m, is_present=True
            ).count()
            rate = round((attended / meeting_count) * 100)
        member_data.append({
            'member': m,
            'is_present': is_present,
            'rate': rate,
        })

    return render(request, 'attendance/meeting_detail.html', {
        'group': group,
        'meeting': meeting,
        'member_data': member_data,
        'visitors': meeting.visitors.all(),
        'visitor_form': attendance_forms.VisitorForm(),
    })


@group_login_required
def add_visitor(request, date):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise Http404

    meeting = get_object_or_404(MeetingDate, group=group, date=parsed_date)

    if request.method == 'POST':
        form = attendance_forms.VisitorForm(request.POST)
        if form.is_valid():
            Visitor.objects.create(
                meeting_date=meeting,
                name=form.cleaned_data['name'],
                note=form.cleaned_data.get('note', ''),
            )
    return redirect('meeting_detail', date=date)


@group_login_required
def members_list(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    members = Member.objects.filter(group=group).order_by('name')
    return render(request, 'attendance/members.html', {
        'group': group,
        'members': members,
    })


@group_login_required
def add_member(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Member.objects.get_or_create(group=group, name=name, defaults={'is_active': True})
    return redirect('members_list')


@group_login_required
def toggle_member(request, member_id):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    member = get_object_or_404(Member, pk=member_id, group=group)
    if request.method == 'POST':
        member.is_active = not member.is_active
        member.save()
    return redirect('members_list')
