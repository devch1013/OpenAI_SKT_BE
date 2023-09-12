from rest_framework import serializers as sz
from ..models import *


class ProjectNameListSz(sz.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "project_name", "purpose"]


class ProjectSaveSz(sz.ModelSerializer):
    class Meta:
        model = Project
        fields = ["project_name", "purpose"]


class ProjectGetSz(sz.ModelSerializer):
    class Meta:
        model = Project
        exclude = ["user"]


class UpdateTableSz(sz.ModelSerializer):
    class Meta:
        model = Project
        fields = ["table"]


class CreateFirstDraftSz(sz.Serializer):
    suggestion_selection = sz.ListField(child=sz.CharField(), required=False, default=[])
    web_pages = sz.ListField(child=sz.CharField(), required=False, default=[])
    files = sz.ListField(child=sz.CharField(), required=False, default=[])
    text = sz.ListField(child=sz.CharField(), required=False, default=[])
    image = sz.ListField(child=sz.CharField(), required=False, default=[])
    youtube = sz.ListField(child=sz.CharField(), required=False, default=[])
