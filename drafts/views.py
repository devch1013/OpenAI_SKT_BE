from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from .models import *
from .serializers.project_sz import *
from .serializers.draft_sz import *
from .serializers.response_sz import *
from .tasks import get_suggestion, write_first_draft
from .apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
import pickle
from django.db.models import Q

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


class DataSourceView(APIView):
    def get(self, request, project_id):
        ...

    def put(self, request, project_id):
        """
        수정
        """
        ...


class FirstDraftView(APIView):
    @swagger_auto_schema(
        operation_summary="Data source 추가 후 첫 draft 생성",
        tags=["Draft"],
        request_body=CreateFirstDraftSz(),
        responses={200: DraftResponseSz()},
    )
    def post(self, request, project_id):
        """
        첫 데이터 소스 업데이트 후 draft 생성
        유저가 고른 suggestion의 id 번호를 int 타입으로 리스트 형태로 주시면 됩니다.
        유저가 추가한 source의 경우는 body 예시를 보시고 각 카테고리에 맞는 데이터를 리스트 형태로 넣어주세요.
        Suggestion 생성과 마찬가지로 시간이 소요되기 때문에 비동기로 처리됩니다.
        요청이 정상적으로 처리되었을 경우 바로 200 응답이 반환됩니다.
        결과는 반환되는 draft_id로 "Draft 생성 완료 확인" API를 참고하시면 됩니다.
        """
        project = Project.objects.get(id=project_id)
        user_files = list()
        source_input_list = ["web_pages", "files", "text", "image", "youtube"]
        draft_input = CreateFirstDraftSz(data=request.data)
        draft_input.is_valid(raise_exception=True)
        
        # for sel in draft_input.data["suggestion_selection"]:
        #     for file in suggestion_instances.filter(source=sel):
        #         user_files.append((file.link, file.data_type))
        for user_input in source_input_list:
            for file in draft_input.data[user_input]:
                user_files.append((file, user_input))
        project.selected_suggestion = "|".join(draft_input.data["suggestion_selection"])
        project.save()

        new_draft = Draft(project=project, status=1)
        new_draft.save()

        write_first_draft.delay(
            project_id=project_id,
            draft_id=new_draft.id,
            user_files=user_files,
        )
        # draft_input.data["web_pages"]
        return JsonResponse(
            {
                "message": "suggestion generation started",
                "draft_id": new_draft.id,
            }
        )


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
        source_list = ["kostat", "youtube", "google", "naver","gallup"]
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


class DraftQueueView(APIView):
    @swagger_auto_schema(
        operation_summary="Draft 생성 완료 확인",
        tags=["Draft"],
        responses={200: DraftContextSz()},
    )
    def get(self, request, draft_id):
        """
        Draft 생성이 완료되었는지 확인하는 엔드포인트
        생성이 완료되었다면 아래 예시와 같은 응답
        생성중이라면 {"status": "WAIT"}의 응답이 갑니다.
        생성중 응답이 반환됐다면 생성완료 응답이 올 때 까지 1초마다 계속 같은 요청 보내시면 됩니다.
        생성완료는 {"status": "COMPLETE"}가 응답에 포함됩니다.
        """
        draft = Draft.objects.get(id=draft_id)
        if draft.status == 0:
            return JsonResponse({"status": "NOT STARTED"})
        if draft.status == 1:
            return JsonResponse({"status": "WAIT"})
        draft_sz = DraftContextSz(draft)
        return JsonResponse(
            {
                "status": "COMPLETE",
                **draft_sz.data,
            }
        )
