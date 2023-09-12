from rest_framework.views import exception_handler
from django.http import HttpResponseServerError
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    print("error message: ",type(exc))
    if isinstance(exc, ObjectDoesNotExist):
        return Response({"message":"ID에 맞는 객체를 찾지 못했습니다."}, status=400)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data["status_code"] = response.status_code

    return response
