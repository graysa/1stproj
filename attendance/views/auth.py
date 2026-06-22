from django.shortcuts import render, redirect
from attendance.forms import LoginForm
from attendance.models import CareGroup


def login_view(request):
    if 'group_id' in request.session:
        return redirect('meeting_list')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group_name = form.cleaned_data['group_name']
        raw_pin = form.cleaned_data['pin']
        try:
            group = CareGroup.objects.get(name=group_name)
        except CareGroup.DoesNotExist:
            form.add_error(None, 'Invalid group or PIN.')
        else:
            if group.check_pin(raw_pin):
                request.session['group_id'] = group.pk
                return redirect('meeting_list')
            else:
                form.add_error(None, 'Invalid group or PIN.')

    return render(request, 'attendance/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('login')
