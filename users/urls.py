from django.urls import path, include
from .views import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # 구글 소셜로그인
    path("google/login/", google_login, name="google_login"),
    path("google/callback/", google_callback, name="google_callback"),
    path("refresh", RefreshToken.as_view()),
    path("userinfo", UserInfo.as_view()),
    path("register", Register.as_view()),
    path("login", Login.as_view()),
    path("email", EmailVerification.as_view()),
    path("logout", logout),
]
