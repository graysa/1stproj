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
    active_member_count = Member.objects.filter(group=group, is_active=True).count()
    avg_attendance = 0
    if total:
        total_present = sum(m.attendance_count() for m in meetings)
        avg_attendance = round(total_present / total, 1)

    # Calendar: default to current month, allow ?y=&m= nav
    today = dt.date.today()
    try:
        cal_year = int(request.GET.get('y', today.year))
        cal_month = int(request.GET.get('m', today.month))
        if cal_month < 1: cal_month = 12; cal_year -= 1
        if cal_month > 12: cal_month = 1; cal_year += 1
        cal_date = dt.date(cal_year, cal_month, 1)
    except (ValueError, TypeError):
        cal_date = today.replace(day=1)
        cal_year, cal_month = cal_date.year, cal_date.month

    # Build set of logged dates this month
    import calendar
    meeting_map = {m.date: m.attendance_count() for m in meetings}
    _, days_in_month = calendar.monthrange(cal_year, cal_month)
    first_weekday = cal_date.weekday()  # 0=Mon

    # Build calendar weeks (list of 7-item lists, None = empty cell)
    cal_days = [None] * first_weekday
    for d in range(1, days_in_month + 1):
        cal_days.append(dt.date(cal_year, cal_month, d))
    while len(cal_days) % 7 != 0:
        cal_days.append(None)
    cal_weeks = [cal_days[i:i+7] for i in range(0, len(cal_days), 7)]

    # Prev/next month urls
    prev_month = cal_date - dt.timedelta(days=1)
    next_month = (cal_date + dt.timedelta(days=31)).replace(day=1)

    return render(request, 'attendance/meeting_list.html', {
        'group': group,
        'meetings': meetings,
        'total_meetings': total,
        'avg_attendance': avg_attendance,
        'active_member_count': active_member_count,
        'meeting_map': meeting_map,
        'cal_weeks': cal_weeks,
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_month_name': cal_date.strftime('%B %Y'),
        'prev_y': prev_month.year,
        'prev_m': prev_month.month,
        'next_y': next_month.year,
        'next_m': next_month.month,
        'today': today,
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
    today = dt.date.today()
    prefill = request.GET.get('date', '')
    try:
        prefill_date = dt.date.fromisoformat(prefill)
        if prefill_date > today:
            prefill_date = today
    except (ValueError, TypeError):
        prefill_date = today
    return render(request, 'attendance/add_meeting_date.html', {
        'group': group,
        'today': today.isoformat(),
        'prefill_date': prefill_date.isoformat(),
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

    # Streak calculation: all meetings BEFORE this one
    past_meetings = list(MeetingDate.objects.filter(group=group, date__lt=parsed_date).order_by('date'))
    past_ids = [m.pk for m in past_meetings]
    past_records = {
        (r['meeting_date_id'], r['member_id']): r['is_present']
        for r in AttendanceRecord.objects.filter(meeting_date_id__in=past_ids).values('meeting_date_id', 'member_id', 'is_present')
    }

    today = dt.date.today()

    member_data = []
    for m in active_members:
        is_present = existing[m.pk].is_present if m.pk in existing else False
        rate = 0.0
        if meeting_count:
            attended = AttendanceRecord.objects.filter(
                meeting_date__in=recent_meetings, member=m, is_present=True
            ).count()
            rate = round((attended / meeting_count) * 100)

        # Streaks from past meetings only
        presences = [past_records.get((mid, m.pk), False) for mid in past_ids]
        current_streak = 0
        for p in reversed(presences):
            if p: current_streak += 1
            else: break
        longest_streak = run = 0
        for p in presences:
            run = run + 1 if p else 0
            longest_streak = max(longest_streak, run)

        is_new = m.date_joined and (today - m.date_joined).days < 30

        member_data.append({
            'member': m,
            'is_present': is_present,
            'rate': rate,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'is_new': is_new,
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
def delete_meeting(request, date):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise Http404
    meeting = get_object_or_404(MeetingDate, group=group, date=parsed_date)
    if request.method == 'POST':
        meeting.delete()
    return redirect('meeting_list')


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
def change_pin(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    error = None
    success = False
    if request.method == 'POST':
        current_pin = request.POST.get('current_pin', '')
        new_pin = request.POST.get('new_pin', '')
        confirm_pin = request.POST.get('confirm_pin', '')
        if not group.check_pin(current_pin):
            error = 'Current PIN is incorrect.'
        elif len(new_pin) < 4:
            error = 'New PIN must be at least 4 characters.'
        elif new_pin != confirm_pin:
            error = 'New PINs do not match.'
        else:
            group.set_pin(new_pin)
            group.save()
            success = True
    return render(request, 'attendance/change_pin.html', {
        'group': group, 'error': error, 'success': success,
    })


@group_login_required
def toggle_member(request, member_id):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    member = get_object_or_404(Member, pk=member_id, group=group)
    if request.method == 'POST':
        member.is_active = not member.is_active
        member.save()
    return redirect('members_list')
