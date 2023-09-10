from rest_framework import serializers as sz
from ..models import *


class UserInfoSz(sz.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "user_profile_image"]
        
        
        
        
class UpdateUserInfoSz(sz.Serializer):
    name = sz.CharField()
    profile_image = sz.CharField()
    description = sz.CharField()
