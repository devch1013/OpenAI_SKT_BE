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

class DraftCreateSz(sz.Serializer):
    id = sz.CharField()

class DraftContextSz(sz.ModelSerializer):
    class Meta:
        model = Draft
        fields = ["id", "name", "draft"]

class DraftTextEditSz(sz.Serializer):
    draft = sz.CharField()
    
    
class DraftEditSz(sz.Serializer):
    query = sz.CharField()
    # draft = sz.CharField()
    draft_part = sz.CharField()
    