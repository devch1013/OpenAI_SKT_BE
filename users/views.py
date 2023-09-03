from django.shortcuts import redirect
from django.conf import settings
from .models import User, EmailCode
from django.http import JsonResponse, HttpResponseRedirect
import os
from datetime import datetime
import uuid
from rest_framework.views import APIView
from users.social_auth.google import get_google_userinfo
from .authentication import JWTAuthentication, RefreshTokenAuthentication
from datetime import timedelta
from .serializers import UserInfoSz
from django.shortcuts import redirect


# 구글 소셜로그인 변수 설정
state = os.environ.get("STATE")
BASE_URL = "https://chat-profile.audrey.kr/"
GOOGLE_CALLBACK_URI = BASE_URL + "api/user/google/callback/"

# FRONT_CALLBACK_URL = "https://audrey.kr/callback"
FRONT_CALLBACK_URL = "http://localhost:51563/callback"


class UserInfo(APIView):
    # authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        userinfo = {
            "email": user.email,
            "name": user.username,
            "user_image": user.user_profile_image,
        }
        return JsonResponse(userinfo, json_dumps_params={"ensure_ascii": False})

    def put(self, request):
        """
        edit user info
        """
        user = request.user
        sz = UserInfoSz(data=request.data).is_valid()
        print(sz.validated_data.name)

        print(request.data)
        return JsonResponse({})

    def delete(self, request):
        """
        delete userinfo
        """
        user = request.user
        user.delete()
        return JsonResponse({})


from random import randint
from django.core.mail import EmailMessage


class EmailVerification(APIView):
    authentication_classes = []

    def post(self, request):
        email = request.data["email"]
        code = randint(100000, 999999)
        try:
            email_code = EmailCode.objects.get(email=email)
            email_code.code = code
        except:
            email_code = EmailCode(email=email, code=code)
        send_email = EmailMessage(
            "Audrey.ai Email Verification Code",
            f"Your Email Verification Code is {code}",
            to=[email],
        )
        send_email.send()
        email_code.save()
        return JsonResponse({"message": "email send success"})

    def put(self, request):
        email = request.data["email"]
        code = str(request.data["code"])
        try:
            email_code = EmailCode.objects.get(email=email)
        except:
            return JsonResponse({"message": "email code not requested"}, status=400)

        if email_code.code == code:
            return JsonResponse({"message": "code verification success"})
        return JsonResponse({"message": "wrong code"}, status=400)


class Register(APIView):
    authentication_classes = []

    def post(self, request):
        login_data = request.data
        email = login_data["email"]

        try:
            User.objects.get(email=email)
            return JsonResponse({"message": "user exists!"}, status=400)
        except:
            ...

        user = User.objects.create_user(
            email=email,
            password=login_data["password"],
            username=email.split("@")[0],
            user_profile_image="",
        )

        access_token, refresh_token = JWTAuthentication.create_jwt(user)
        print(access_token)
        response = HttpResponseRedirect(
            f"{FRONT_CALLBACK_URL}?access_token={access_token}&refresh_token={refresh_token}"
        )
        return response


class Login(APIView):
    authentication_classes = []

    def post(self, request):
        login_data = request.data
        email = login_data["email"]
        password = login_data["password"]

        try:
            user = User.objects.get(email=email)

        except:
            return JsonResponse({"message": "user not exists!"}, status=400)

        if user.check_password(password):
            access_token, refresh_token = JWTAuthentication.create_jwt(user)
            print(access_token)
            response = HttpResponseRedirect(
                f"{FRONT_CALLBACK_URL}?access_token={access_token}&refresh_token={refresh_token}"
            )
            return response

        return JsonResponse({"message": "wrong password"}, status=400)


class RefreshToken(APIView):
    authentication_classes = [RefreshTokenAuthentication]

    def get(self, request):
        jwt_token, refresh_token = JWTAuthentication.create_jwt(request.user)
        return get_token_response(jwt_token, refresh_token)


def logout(request):
    if request.session.get("userId"):
        del request.session["userId"]
        return JsonResponse({"message": "logout success"})
    return JsonResponse({"message": "not logined"})


def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
    client_id = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
    print(client_id)
    response = redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}"
    )
    response["Origin"] = "https://san9min.github.io"
    return response


def google_callback(request):
    userinfo_req_json = get_google_userinfo(request.GET.get("code"))

    # 3. 전달받은 이메일, access_token, code를 바탕으로 회원가입/로그인
    try:
        user = User.objects.get(email=userinfo_req_json.get("email"))
    except User.DoesNotExist:
        user = create_user(userinfo_req_json)

    access_token, refresh_token = JWTAuthentication.create_jwt(user)
    response = HttpResponseRedirect(
        f"{FRONT_CALLBACK_URL}?access_token={access_token}&refresh_token={refresh_token}"
    )
    return response


def create_user(user_info: dict):
    return User.objects.create_user(
        email=user_info.get("email"),
        username=user_info.get("name"),
        user_profile_image=user_info.get("picture"),
    )


def get_token_response(access_token, refresh_token, refresh_exp=30):
    expires = datetime.utcnow() + timedelta(days=refresh_exp)
    response = JsonResponse({"access_token": access_token})

    ## 쿠키에 refresh token 저장
    response.set_cookie("refresh", refresh_token, expires=expires)
    return response
