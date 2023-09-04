from rest_framework import serializers as sz
from ..models import *


class DraftGetSz(sz.ModelSerializer):
    class Meta:
        model = Draft
        fields = "__all__"


class DraftListSz(sz.ModelSerializer):
    class Meta:
        model = Draft
        fields = ["id", "name", "timestamp"]


class DraftContextSz(sz.ModelSerializer):
    class Meta:
        model = Draft
        fields = ["id", "name", "draft"]
