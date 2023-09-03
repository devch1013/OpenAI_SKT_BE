from rest_framework import serializers as sz
from ..models import *


class ProjectNameListSz(sz.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "project_name"]


class ProjectSaveSz(sz.ModelSerializer):
    class Meta:
        model = Project
        exclude = ["table"]


class ProjectGetSz(sz.ModelSerializer):
    class Meta:
        model = Project
        exclude = ["user"]


class UpdateTableSz(sz.ModelSerializer):
    class Meta:
        model = Project
        fields = ["table"]
