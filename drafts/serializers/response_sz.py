from rest_framework import serializers as sz
from ..models import *

class SuccessResponseSz(sz.Serializer):
    message = sz.CharField()
class ProjectCreateResponse(sz.Serializer):
    project_id = sz.IntegerField()
    table = sz.CharField()

class SuggestionInstanceSz(sz.ModelSerializer):
    class Meta:
        model = DataSourceSuggestion
        exclude = ["id", "project", "source", "data_type"]

class SuggestionResponseSz(sz.Serializer):
    status = sz.CharField()
    kostat = SuggestionInstanceSz(many=True)
    youtube = SuggestionInstanceSz(many=True)
    google = SuggestionInstanceSz(many=True)
    naver = SuggestionInstanceSz(many=True)


class DraftResponseSz(sz.Serializer):
    message = sz.CharField()
    draft_id = sz.IntegerField()