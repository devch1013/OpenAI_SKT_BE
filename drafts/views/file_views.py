from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from ..models import *
from ..serializers.project_sz import *
from ..serializers.draft_sz import *
from ..serializers.response_sz import *
from ..serializers.datasource_sz import *
from ..tasks import get_suggestion
from ..apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import os
import uuid
import urllib



class DataSourceFileView(APIView):
    authentication_classes = []
    def get(self, request, source_id):
        datasource = DataSource.objects.get(id=source_id)
        project_id = datasource.project.id
        storage = f"audrey_files/source_files/{project_id}"
        file_path = datasource.data
        if "pdf" in datasource.filename:
            file_type = "application/pdf"  # django file object에 content type 속성이 없어서 따로 저장한 필드
        elif "png" in datasource.filename:
            file_type = "image/png"
        else:
            file_type = "application/octet-stream"
        # filename = str(datasource.filename)
        filename = urllib.parse.quote(datasource.filename.encode('utf-8'))
        fs = FileSystemStorage(storage)
        response = FileResponse(fs.open(file_path.split("/")[-1], 'rb'), content_type=file_type)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
    
    
class ProfileImageView(APIView):
    authentication_classes = []
    def get(self, request):
        storage = f"audrey_files/images"
        file_type = "image/png"  # django file object에 content type 속성이 없어서 따로 저장한 필드
        fs = FileSystemStorage(storage)
        filename = "base_profile.png"
        response = FileResponse(fs.open(filename, 'rb'), content_type=file_type)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
    
class ImageView(APIView):
    authentication_classes = []
    def get(self, request, filename):
        storage = f"audrey_files/images"
        file_type = "image/png"  # django file object에 content type 속성이 없어서 따로 저장한 필드
        fs = FileSystemStorage(storage)
        response = FileResponse(fs.open(filename, 'rb'), content_type=file_type)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response