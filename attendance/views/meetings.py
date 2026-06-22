from django.shortcuts import render, get_object_or_404
from attendance.decorators import group_login_required
from attendance.models import CareGroup, MeetingDate


@group_login_required
def meeting_list(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    meetings = MeetingDate.objects.filter(group=group).order_by('-date')
    return render(request, 'attendance/meeting_list.html', {
        'group': group,
        'meetings': meetings,
    })
