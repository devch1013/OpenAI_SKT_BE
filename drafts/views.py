from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from .models import *
from .serializers.project_sz import *
from .serializers.draft_sz import *
from .serializers.response_sz import *
from .tasks import add as od
from .apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
import pickle

# Create your views here.


def test(request):
    od.delay(1, 3)
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
        request body의 user는 자동으로 들어가니 안주셔도 됩니다.
        프로젝트 이름과 purpose를 주면 목차를 생성하고 생성된 프로젝트 id와 함께 반환됩니다.
        """
        user = request.user
        project = ProjectSaveSz(data={**request.data, "user": user.id})
        project.is_valid(raise_exception=True)
        project_db = project.save()
        print(project.validated_data.get("purpose"))
        project_instance = ProjectAi(
            user_id="test_2",
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


class RecentDraft(APIView):
    def get(self, request, project_id):
        draft = Draft.objects.filter(project__id=project_id).order_by("-timestamp")
        recent_draft = draft[0]
        draft_sz = DraftGetSz(recent_draft)
        return JsonResponse(draft_sz.data)


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
    def post(self, request, project_id):
        """
        업데이트 된 index 받아서 저장 후 suggestion 생성(처음에만)
        들어오묜
        """
        project = Project.objects.get(id=project_id)
        project_sz = UpdateTableSz(project, data=request.data)
        if project_sz.is_valid():
            project_sz.save()
        ## TODO Suggestion 생성 시작 (비동기)
        return JsonResponse({"message": "suggestion generation started"})

    def put(self, project_id):
        """
        단순 목차 텍스트 업데이트
        """
        ...


class DataSourceView(APIView):
    def get(self, request, project_id):
        ...

    def put(self, request, project_id):
        """
        수정
        """
        ...

    def post(self, request, project_id):
        """
        첫 데이터 소스 업데이트
        + draft 생성
        """
        ...


class DraftView(APIView):
    def get(self, request, project_id):
        """
        draft 제목, 생성일
        """
        draft = Draft.objects.filter(project__id=project_id).order_by("-timestamp")
        draft_sz = DraftListSz(draft, many=True)
        return JsonResponse(draft_sz.data, safe=False)

    def post(self, request, project_id):
        """
        첫 draft 생성
        """
        ...


class SingleDraftView(APIView):
    def get(self, request, draft_id):

        ...

    def post(self, request, draft_id):
        """
        draft와 ai 요청사항 반영해서 draft 생성
        """
        ...

    def put(self, request, draft_id):
        """
        단순 텍스트 수정
        """
        ...


class SuggestionQueueView(APIView):
    def get(self, request, project_id):
        """
        Suggestion 생성이 완료되었는지 확인하는 엔드포인트
        생성이 완료되었다면 아래 예시와 같은 응답
        생성중이라면 {"status": "WAIT"}의 응답이 갑니다.
        """
        project = Project.objects.get(id=project_id)
        if project.suggestion_flag == True:
            suggestions = DataSourceSuggestion.objects.filter(project=project)
            suggestion_sz = SuggestionResponseSz(
                suggestions, data={"status": "COMPLETE"}, many=True
            )
            return JsonResponse(suggestion_sz.data, safe=False)
        return JsonResponse({"status": "WAIT"})
