from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Extract the JWT from the Authorization header
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        if jwt_token is None:
            raise AuthenticationFailed("Token not found in header")

        jwt_token = JWTAuthentication.get_the_token_from_header(jwt_token)  # clean the token

        # Decode the JWT and verify its signature
        try:
            payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError:
            raise AuthenticationFailed("Invalid signature")
        except:
            raise ParseError()

        # Get the user from the database
        user_id = payload.get("user_id")
        if user_id is None:
            raise AuthenticationFailed("User id not found in JWT")

        user = User.objects.filter(id=user_id).first()
        if user is None:
            raise AuthenticationFailed("User not found")

        # Return the user and token payload
        return user, payload

    def authenticate_header(self, request):
        return "Bearer"

    @classmethod
    def create_jwt(cls, user):
        # Create the JWT payload
        payload = {
            "user_id": user.id,
            "exp": int(
                (
                    datetime.now() + timedelta(hours=settings.JWT_CONF["TOKEN_LIFETIME_HOURS"])
                ).timestamp()
            ),
            # set the expiration time for 5 hour from now
            "iat": datetime.now().timestamp(),
        }

        # Encode the JWT with your secret key
        access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        payload["type"] = "refresh"
        refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return access_token, refresh_token

    @classmethod
    def get_the_token_from_header(cls, token):
        token = token.replace("Bearer", "").replace(" ", "")  # clean the token
        return token


class RefreshTokenAuthentication(JWTAuthentication):
    def authenticate(self, request):
        refresh_token = request.COOKIES.get("refresh") or None
        print(refresh_token)
        if refresh_token is None:
            raise AuthenticationFailed("Refresh token is not in cookie")

        decoded_jwt = jwt.decode(
            jwt=refresh_token,
            key=settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        try:
            user = User.objects.get(**{"id": decoded_jwt.get("user_id")})
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed("User is inactive", code="user_inactive")
        return user, refresh_token
