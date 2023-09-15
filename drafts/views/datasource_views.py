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
# Create your views here.




class SuggestionView(APIView):
    @swagger_auto_schema(
        operation_summary="Table 수정 후 Suggestion 생성(project당 한번만 사용)",
        tags=["Project"],
        request_body=UpdateTableSz(),
        responses={200: SuccessResponseSz()},
    )
    def post(self, request, project_id):
        """
        업데이트 된 index 받아서 저장 후 suggestion 생성(처음에만)
        Suggestion 생성에 시간이 소요되기 때문에 비동기로 처리됩니다.
        요청이 정상적으로 처리되었을 경우 바로 200 응답이 반환됩니다.
        suggestion 결과는 "suggestion 생성 완료 확인" API를 사용하시면 됩니다.
        """
        print("table update request")
        project = Project.objects.get(id=project_id)
        if project.suggestion_flag == True:
            return JsonResponse({"message": "suggestion already created"}, status=400)
        project_sz = UpdateTableSz(project, data=request.data)
        if project_sz.is_valid(raise_exception=True):
            project = project_sz.save()

        get_suggestion.delay(
            project_id=project_id,
            purpose=project.purpose,
            table=project.table,
        )
        return JsonResponse({"message": "suggestion generation started"})


    @swagger_auto_schema(
        operation_summary="Suggestion 선택",
        tags=["Project"],
        request_body=SuggestionSz(),
        responses={200: SuccessResponseSz()},
    )
    def put(self, request, project_id):
        """
        suggestion select
        """
        project = Project.objects.get(id=project_id)
        selection = SuggestionSz(data=request.data)
        selection.is_valid(raise_exception=True)
        project.selected_suggestion = "|".join(list(map(str,selection.data["suggestion_selection"])))
        project.save()
        
        return SuccessResponse()

    def get(self, project_id):
        ...


class SuggestionQueueView(APIView):
    @swagger_auto_schema(
        operation_summary="Suggestion 생성 완료 확인",
        tags=["Project"],
        responses={200: SuggestionResponseSz()},
    )
    def get(self, request, project_id):
        """
        Suggestion 생성이 완료되었는지 확인하는 엔드포인트
        생성이 완료되었다면 아래 예시와 같은 응답
        생성중이라면 {"status": "WAIT"}의 응답이 갑니다.
        생성중 응답이 반환됐다면 생성완료 응답이 올 때 까지 1초마다 계속 같은 요청 보내시면 됩니다.
        생성완료는 {"status": "COMPLETE"}가 응답에 포함됩니다.
        """
        project = Project.objects.get(id=project_id)
        source_list = ["kostat", "youtube", "google", "naver", "gallup"]
        if project.suggestion_flag == True:
            suggestions = DataSourceSuggestion.objects.filter(project=project)
            sz_data = {"status": "COMPLETE"}
            for source in source_list:
                sz_data[source] = SuggestionInstanceSz(
                    suggestions.filter(source=source), many=True
                ).data
            print(sz_data)
            suggestion_sz = SuggestionResponseSz(data=sz_data)
            suggestion_sz.is_valid()
            return JsonResponse(suggestion_sz.data, json_dumps_params={"ensure_ascii": False})
        return JsonResponse({"status": "WAIT"})

source_input_list = ["web_pages", "files", "text", "image", "youtube"]
source_list = ["web_pages", "text", "youtube"]
file_keys = ["files", "images"]

class DataSourceView(APIView):
    def get(self, request, project_id):
        project = Project.objects.get(id = project_id)
        sources = DataSource.objects.filter(project=project)
        if project.selected_suggestion == None:
            selected_suggestion_id_list = []
        else:
            selected_suggestion_id_list = list(map(int,project.selected_suggestion.split("|")))
        suggestion = DataSourceSuggestion.objects.filter(id__in = selected_suggestion_id_list)
        response_dict = dict()
        response_dict["suggestion"] = list()
        for sug in suggestion:
            response_dict["suggestion"].append({
                "source": sug.source,
                "title": sug.title,
                "description": sug.description,
                "link": sug.link,
            })
            
        for source_name in source_input_list:
            response_dict[source_name] = list()
            source_instances = sources.filter(data_type=source_name)
            for source_inst in source_instances:
                response_dict[source_name].append(
                    {
                        "id": source_inst.id,
                        "source": source_inst.data,
                    }
                )
        return JsonResponse(response_dict)
    
    @swagger_auto_schema(
        operation_summary="Datasource 추가",
        tags=["DataSource"],
        request_body=DataSourceSz(),
        responses={200: SuccessResponseSz()},
    )
    def post(self, request, project_id):
        
        project = Project.objects.get(id = project_id)
        draft_input = DataSourceSz(data=request.data)
        draft_input.is_valid(raise_exception=True)
        files = dict(request.FILES)
        storage = f"audrey_files/source_files/{project_id}"
        for key, filelist in files.items():
            for file in filelist:
                if key in file_keys:
                    print(key, file.name)
                    ds_instance = DataSource(project = project)
                    ds_instance.save()
                    meme = file.name.split(".")[-1]
                    fs = FileSystemStorage(location=storage, base_url=storage)
                    # FileSystemStorage.save(file_name, file_content)
                    filename = fs.save(f"{ds_instance.id}.{meme}", file)
                    if meme == "pdf":
                        ds_instance.data_type = "pdf_file"
                    else:
                        ds_instance.data_type = key
                    ds_instance.data = os.path.join(storage, filename)
                    ds_instance.filename = file.name
                    ds_instance.save()
        
        for user_input in source_list:
            for file in draft_input.data[user_input]:
                print(user_input, file)
                ds_instance = DataSource(data_type=user_input, data=file, project=project)
                ds_instance.save()
                
        draft_id = str(uuid.uuid4())
        
        return JsonResponse({"id": draft_id})
    
    
    @swagger_auto_schema(
        operation_summary="Datasource 삭제",
        tags=["DataSource"],
        request_body=DataSourceDeleteSz(),
        responses={200: SuccessResponseSz()},
    )
    def delete(self, request, project_id):
        
        project = Project.objects.get(id = project_id)
        datasource_sz = DataSourceDeleteSz(data=request.data)
        datasource_sz.is_valid(raise_exception=True)
        
        delete_list = datasource_sz.data.get("delete_id")
        DataSource.objects.filter(project=project).filter(id__in = delete_list).delete()
    
        return SuccessResponse()
    
    
