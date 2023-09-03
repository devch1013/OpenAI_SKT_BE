from django.http import JsonResponse


class SuccessResponse(JsonResponse):
    def __init__(self):
        super().__init__({"message": "success!"})
