from rest_framework import serializers as sz
from ..models import *


class ProjectCreateResponse(sz.Serializer):
    project_id = sz.IntegerField()
    table = sz.CharField()


class SuggestionResponseSz(sz.ModelSerializer):
    status = sz.CharField()

    class Meta:
        model = DataSourceSuggestion
        exclude = ["id", "project"]
