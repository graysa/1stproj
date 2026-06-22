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
    return render(request, 'attendance/meeting_list.html', {
        'group': group,
        'meetings': meetings,
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

    member_data = [
        {
            'member': m,
            'is_present': existing[m.pk].is_present if m.pk in existing else False,
        }
        for m in active_members
    ]

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
