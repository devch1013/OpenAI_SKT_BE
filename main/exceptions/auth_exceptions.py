from rest_framework.exceptions import APIException
from rest_framework import status


class NotAuthenticatedException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "User Not Autheticated"
    default_code = "error"
