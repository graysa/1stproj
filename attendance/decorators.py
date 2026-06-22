from functools import wraps
from django.shortcuts import redirect


def group_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'group_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
