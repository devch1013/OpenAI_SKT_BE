from rest_framework import serializers as sz


class UserInfoSz(sz.Serializer):
    name = sz.CharField()
    profile_image = sz.CharField()
    description = sz.CharField()
