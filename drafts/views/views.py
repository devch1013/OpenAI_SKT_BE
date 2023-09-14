from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from ..models import *
from ..serializers.project_sz import *
from ..serializers.draft_sz import *
from ..serializers.response_sz import *
from ..tasks import get_suggestion
from ..apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
# Create your views here.


def test(request):
    # od.delay(1, 3)
    return JsonResponse({})


class Projects(APIView):
    @swagger_auto_schema(
        operation_description="현재 로그인 된 사용자의 프로젝트 리스트 이름 반환",
        operation_summary="프로젝트 리스트 반환",
        tags=["Project"],
        responses={200: ProjectNameListSz(many=True)},
    )
    def get(self, request):
        project = Project.objects.filter(user=request.user)
        sz = ProjectNameListSz(project, many=True)
        return JsonResponse(sz.data, safe=False)

    @swagger_auto_schema(
        operation_summary="새 프로젝트 생성",
        tags=["Project"],
        request_body=ProjectSaveSz(),
        responses={200: ProjectCreateResponse()},
    )
    def post(self, request):
        """
        프로젝트 이름과 purpose를 주면 목차를 생성하고 생성된 프로젝트 id와 함께 반환됩니다.
        """
        user = request.user
        project = ProjectSaveSz(data=request.data)
        project.is_valid(raise_exception=True)
        project_db = project.save(user=user)
        print(project.validated_data.get("purpose"))
        project_instance = ProjectAi(
            project_id=project_db.id,
            **(DraftsConfig.instances),
        )
        project_instance.set_purpose(purpose=project.validated_data.get("purpose"))
        table = project_instance.get_table()
        project_db.table = table
        project_db.save()
        print(table)
        response_sz = ProjectCreateResponse(data={"project_id": project_db.id, "table": table})
        response_sz.is_valid()
        return JsonResponse(response_sz.data, json_dumps_params={"ensure_ascii": False})

    def delete(self, request):
        project = ProjectGetSz(data=request.data)
        project.is_valid(raise_exception=True)
        # project_model = project.instance
        print(project.data)
        return SuccessResponse()


class SingleProject(APIView):
    def get(self, request, project_id):
        project = Project.objects.get(id=id)
        project_sz = ProjectGetSz(project)
        return JsonResponse(project_sz.data)

    def put(self, request, id: int) -> JsonResponse:
        """ """
        ...

    def delete(self, request, project_id):
        project = Project.objects.get(id=project_id)
        project.delete()
        return SuccessResponse()


class TableView(APIView):
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

        print("celery start")
        get_suggestion.delay(
            project_id=project_id,
            purpose=project.purpose,
            table=project.table,
        )
        print("celery end")
        return JsonResponse({"message": "suggestion generation started"})

    def put(self, project_id):
        """
        단순 목차 텍스트 업데이트
        """
        ...

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


