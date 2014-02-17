from django.utils.decorators import available_attrs
from functools import wraps
from django.http import Http404

def user_passes_test(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            raise Http404
        return _wrapped_view
    return decorator

def perm_required(rol, raise_exception=True):
    """
    Decorator for views that checks whether a user has a particular role
    enabled, redirecting to the log-in page if neccesary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """
    def check_perms(user):
        if not isinstance(rol, (list, tuple)):
            roles = [rol]
        else:
            roles = rol

        #first check anonymous user
        if 'anonymous' in roles and user.is_anonymous():
            return True

        # First check if the user has the roles (even anon users)
        if user.has_rol(roles):
            return True
        # In case the 404 handler should be called raise the exception
        if raise_exception:
            raise Http404
        # As the last resort, show the raise 404 exception
        return False
    return user_passes_test(check_perms)
