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
