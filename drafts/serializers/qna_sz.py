from rest_framework import serializers as sz



class QnARequestSz(sz.Serializer):
    question = sz.CharField(required=True)