from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from django.http.response import StreamingHttpResponse
from ..models import *
from ..serializers.project_sz import *
from ..serializers.draft_sz import *
from ..serializers.response_sz import *
from ..tasks import get_suggestion, write_first_draft
from ..apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
import pickle
from django.db.models import Q
import threading
from time import time
from ..utils.streaming_queue import StreamingQueue


class RecentDraft(APIView):
    def get(self, request, project_id):
        draft = Draft.objects.filter(project__id=project_id).order_by("-timestamp")
        recent_draft = draft[0]
        draft_sz = DraftGetSz(recent_draft)
        return JsonResponse(draft_sz.data)
    
    
    

source_input_list = ["web_pages", "files", "text", "image", "youtube"]
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

        draft_input = CreateFirstDraftSz(data=request.data)
        draft_input.is_valid(raise_exception=True)

        # for sel in draft_input.data["suggestion_selection"]:
        #     for file in suggestion_instances.filter(source=sel):
        #         user_files.append((file.link, file.data_type))

        for user_input in source_input_list:
            for file in draft_input.data[user_input]:
                new_source = DataSource(data_type=user_input, data=file, project=project)
                new_source.save()
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

    def put(self, request, project_id):
        """
        수정
        """
        ...
        
        

class DraftTestView(APIView):
    def post(self, request, project_id):
        project = Project.objects.get(id=project_id)
        user_files = list()

        draft_input = CreateFirstDraftSz(data=request.data)
        draft_input.is_valid(raise_exception=True)

        # for sel in draft_input.data["suggestion_selection"]:
        #     for file in suggestion_instances.filter(source=sel):
        #         user_files.append((file.link, file.data_type))

        for user_input in source_input_list:
            for file in draft_input.data[user_input]:
                new_source = DataSource(data_type=user_input, data=file, project=project)
                new_source.save()
                user_files.append((file, user_input))
        project.selected_suggestion = "|".join(draft_input.data["suggestion_selection"])
        project.save()

        new_draft = Draft(project=project, status=1)
        new_draft.save()

        project_instance = Project.objects.get(id=project_id)
        draft_id=new_draft.id
        suggestion_instances = DataSourceSuggestion.objects.filter(project=project_instance)
        suggestion_file_dict = dict()
        for sel in project_instance.selected_suggestion.split("|"):
            si = suggestion_instances.get(id=int(sel))
            if si.keyword not in suggestion_file_dict.keys():
                suggestion_file_dict[si.keyword] = dict()
            # suggestion_file_dict[sel] = list()
            # for file in suggestion_instances.filter(source=sel):
            if si.source in suggestion_file_dict[si.keyword].keys():
                suggestion_file_dict[si.keyword][si.source].append(
                    {"data_path": si.link, "data_type": si.data_type}
                )
            else:
                suggestion_file_dict[si.keyword][si.source] = [{"data_path": si.link, "data_type": si.data_type}]
        print(suggestion_file_dict)
        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"user/{project.id}/user_instance.json",
        )

        project.add_files(user_files)
        database = project.parse_files_to_embedchain()
        # draft = project.get_draft(draft_id=draft_id)
        
        def get_draft_stream(project):
            streaming_queue = StreamingQueue()
            content = ""
            def chat_task():
                project.get_draft(draft_id=draft_id, queue=streaming_queue)
                # project.get_qna_answer(
                #     question=question,
                #     qna_history=qna_history,
                #     queue=streaming_queue,
                # )
                streaming_queue.end_job()

            start = time()
            t = threading.Thread(target=chat_task)
            t.start()
            while True:
                if streaming_queue.is_end():
                    print("streaming is ended")
                    break
                ## 4개
                if not streaming_queue.is_empty():
                    next_token = streaming_queue.get()
                    content += next_token
                    print(next_token)
                    yield next_token
                    
            print(content)
                    
        result = get_draft_stream(project)
        # project.save()

        # draft_instance = Draft.objects.get(id=draft_id)
        # draft_instance.table = project_instance.table
        # draft_instance.draft = draft
        # draft_instance.status = 2
        # draft_instance.name = "Draft 1"
        # draft_instance.save()
        # print(content)
        # draft_input.data["web_pages"]
        response = StreamingHttpResponse(result, status=200, content_type="text/event-stream")
        return response

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


import json


class SingleDraftView(APIView):
    def get(self, request, draft_id):
        draft = Draft.objects.get(id=draft_id)
        response_dict = dict()
        response_dict["draft"] = draft.draft
        with open(f"user/{draft.project.id}/user_instance.json", "r") as user_instance:
            user_instance = json.load(user_instance)
        response_dict["table"] = user_instance["tables"]
        draft_part = user_instance["draft_parts"]
        response_dict["source"] = list()
        for part in draft_part:
            sources = part["files"]
            for source in sources:
                del source["id"]
                del source["token_num"]
            response_dict["source"].append(
                {
                    "single_table": part["single_table"],
                    "sources": sources,
                }
            )
        # print(user_instance)
        return JsonResponse(response_dict)

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
