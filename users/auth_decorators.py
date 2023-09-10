from .models import User, UserSession
from django.shortcuts import redirect
from rest_framework.exceptions import NotAuthenticated


def auth_user(func):
    """
    add user parameter
    """

    def wrapper(self, request, **kwargs):
        session_id = request.session.get("userId")
        try:
            user = UserSession.objects.get(session_id=session_id)
            user = user.user
        except:
            user = None
        return func(self, request, user, **kwargs)

    return wrapper
