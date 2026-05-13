from django.shortcuts import redirect
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin():
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


def cashier_or_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile'):
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper