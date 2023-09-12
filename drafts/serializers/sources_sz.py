from rest_framework import serializers as sz
from ..models import *


class DataSourceListSz(sz.Serializer):
    selected_source = sz.ListField