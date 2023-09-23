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
    
class DalleImageSz(sz.ModelSerializer):
    class Meta:
        model = DalleImage
        fields = ["id", "link"]

class ImageSelectionSz(sz.Serializer):
    image_id = sz.IntegerField()
    
    
    
    
############ For swagger

class DataSourcesSz(sz.Serializer):
    data = sz.CharField()
    data_path = sz.CharField()
    data_type = sz.CharField()
    
class DataSourceGetSz(sz.Serializer):
    single_table = sz.CharField()
    sources = DataSourcesSz(many=True)
    
class SingleDraftGetSz(sz.Serializer):
    draft = sz.CharField()
    table = sz.ListField(child = sz.CharField())
    source = DataSourceGetSz(many=True)
    
    

