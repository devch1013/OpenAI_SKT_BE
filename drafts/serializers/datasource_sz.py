from rest_framework import serializers as sz
from ..models import *

class SuggestionSz(sz.Serializer):
    suggestion_selection = sz.ListField(child=sz.IntegerField(), required=False, default=[])


class DataSourceSz(sz.Serializer):
    web_pages = sz.ListField(child=sz.CharField(), required=False, default=[])
    text = sz.ListField(child=sz.CharField(), required=False, default=[])
    youtube = sz.ListField(child=sz.CharField(), required=False, default=[])

# class CreateFirstDraftSz(sz.Serializer):
#     suggestion_selection = sz.ListField(child=sz.CharField(), required=False, default=[])
#     web_pages = sz.ListField(child=sz.CharField(), required=False, default=[])
#     files = sz.ListField(child=sz.CharField(), required=False, default=[])
#     text = sz.ListField(child=sz.CharField(), required=False, default=[])
#     image = sz.ListField(child=sz.CharField(), required=False, default=[])
#     youtube = sz.ListField(child=sz.CharField(), required=False, default=[])

class DataSourceDeleteSz(sz.Serializer):
    delete_id = sz.ListField(child=sz.IntegerField(), required=True)