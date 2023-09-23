from rest_framework.views import APIView
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from django.http.response import StreamingHttpResponse
from ..models import *
from ..serializers.project_sz import *
from ..serializers.draft_sz import *
from ..serializers.response_sz import *
from ..apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
import os
import threading
from time import time
from ..utils.streaming_queue import StreamingQueue
import logging
logger = logging.getLogger('my')    

class RecentDraft(APIView):
    @swagger_auto_schema(
        operation_summary="가장 최근 드래프트",
        deprecated=True,
    )
    def get(self, request, project_id):
        draft = Draft.objects.filter(project__id=project_id).order_by("-timestamp")
        recent_draft = draft[0]
        draft_sz = DraftGetSz(recent_draft)
        return JsonResponse(draft_sz.data)


source_input_list = ["web_pages", "files", "text", "image", "youtube"]


# class FirstDraftView(APIView):
#     @swagger_auto_schema(
#         operation_summary="Data source 추가 후 첫 draft 생성",
#         tags=["Draft"],
#         request_body=CreateFirstDraftSz(),
#         responses={200: DraftResponseSz()},
#     )
#     def post(self, request, project_id):
#         """
#         첫 데이터 소스 업데이트 후 draft 생성
#         유저가 고른 suggestion의 id 번호를 int 타입으로 리스트 형태로 주시면 됩니다.
#         유저가 추가한 source의 경우는 body 예시를 보시고 각 카테고리에 맞는 데이터를 리스트 형태로 넣어주세요.
#         Suggestion 생성과 마찬가지로 시간이 소요되기 때문에 비동기로 처리됩니다.
#         요청이 정상적으로 처리되었을 경우 바로 200 응답이 반환됩니다.
#         결과는 반환되는 draft_id로 "Draft 생성 완료 확인" API를 참고하시면 됩니다.
#         """
#         project = Project.objects.get(id=project_id)
#         user_files = list()

#         draft_input = CreateFirstDraftSz(data=request.data)
#         draft_input.is_valid(raise_exception=True)

#         # for sel in draft_input.data["suggestion_selection"]:
#         #     for file in suggestion_instances.filter(source=sel):
#         #         user_files.append((file.link, file.data_type))

#         for user_input in source_input_list:
#             for file in draft_input.data[user_input]:
#                 new_source = DataSource(data_type=user_input, data=file, project=project)
#                 new_source.save()
#                 user_files.append((file, user_input))
#         project.selected_suggestion = "|".join(draft_input.data["suggestion_selection"])
#         project.save()

#         new_draft = Draft(project=project, status=1)
#         new_draft.save()

#         write_first_draft.delay(
#             project_id=project_id,
#             draft_id=new_draft.id,
#             user_files=user_files,
#         )
#         # draft_input.data["web_pages"]
#         return JsonResponse(
#             {
#                 "message": "suggestion generation started",
#                 "draft_id": new_draft.id,
#             }
#         )





class DraftView(APIView):
    def get(self, request, project_id):
        """
        draft 제목, 생성일
        """
        draft = Draft.objects.filter(project__id=project_id).order_by("-timestamp")
        draft_sz = DraftListSz(draft, many=True)
        return JsonResponse(draft_sz.data, safe=False)

    @swagger_auto_schema(
        operation_summary="draft 생성",
        tags=["Draft"],
    )
    def post(self, request, project_id):
        """
        draft 생성
        """
        
        project_instance = Project.objects.get(id=project_id)
        user_files = list()

        datasources = DataSource.objects.filter(project=project_instance)
        for datasource in datasources:
            user_files.append((datasource.data, datasource.data_type))

        new_draft = Draft(project=project_instance, status=1, table=project_instance.table)
        new_draft.save()
        draft_id = new_draft.id
        logger.info(f"project {project_instance.id}, draft {new_draft.id} write request accepted")
        suggestion_instances = DataSourceSuggestion.objects.filter(project=project_instance)
        if project_instance.selected_suggestion != None and project_instance.selected_suggestion != "":
            for sel in project_instance.selected_suggestion.split("|"):
                si = suggestion_instances.get(id=int(sel))
                user_files.append((si.link, si.data_type))

        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"audrey_files/project/{project_instance.id}/user_instance.json",
        )

        project.add_files(user_files)
        project.parse_files_to_embedchain()
        logger.info(f"project {project_instance.id}, draft {new_draft.id} embedding finished")

        result = get_draft_stream(project, draft_id, new_draft)

        response = StreamingHttpResponse(result, status=200, content_type="text/event-stream")
        return response

def get_draft_stream(project: ProjectAi, draft_id: int, new_draft: Draft):
    streaming_queue = StreamingQueue()
    content = ""

    yield f"###{draft_id}"

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
            yield next_token

    project.save()
    new_draft.draft = content
    new_draft.status = 2
    new_draft.save()
    logger.info(f"project {new_draft.project.id}, draft {new_draft.id} generation finished")

import json


class SingleDraftView(APIView):
    @swagger_auto_schema(
        operation_summary="Draft 정보 요청",
        tags=["Draft"],
        responses={200: SingleDraftGetSz()},
    )
    def get(self, request, draft_id):
        draft = Draft.objects.get(id=draft_id)
        if draft.status != 2:
            return JsonResponse({"message": "draft "})
        response_dict = dict()
        response_dict["draft"] = draft.draft
        with open(
            f"audrey_files/project/{draft.project.id}/drafts/draft_{draft.id}.json", "r"
        ) as draft_file:
            draft_file = json.load(draft_file)
        response_dict["table"] = draft_file["tables"]
        draft_part = draft_file["draft_parts"]
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
            
        try:
            dalle_image = DalleImage.objects.get(id=draft.thumbnail)
            response_dict["image_link"] = dalle_image.link
        except:
            response_dict["image_link"] = None
            
            
        
        # print(user_instance)
        return JsonResponse(response_dict)

    @swagger_auto_schema(
        operation_summary="Draft Edit(with AI)",
        tags=["Draft"],
        request_body=DraftEditSz(),
        responses={200: SuccessResponseSz()},
    )
    def post(self, request, draft_id):
        """
        draft와 ai 요청사항 반영해서 draft 수정
        """
        print("draft edit started")
        draft_instance = Draft.objects.get(id=draft_id)
        project_instance = draft_instance.project
        edit_query = DraftEditSz(data=request.data)
        edit_query.is_valid(raise_exception=True)
        print(edit_query)
        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"audrey_files/project/{project_instance.id}/user_instance.json",
        )
        editted_draft = project.edit_draft(
            edit_query.data.get("query"),
            edit_query.data.get("draft_part"),
        )
        editted_draft = editted_draft.replace("/home/ubuntu/draft/audrey_files", "https://chat-profile.audrey.kr/api/project")
        return JsonResponse({"draft": editted_draft})

    @swagger_auto_schema(
        operation_summary="Draft 단순 텍스트 수정",
        tags=["Draft"],
        request_body=DraftTextEditSz(),
        responses={200: SuccessResponseSz()},
    )
    def put(self, request, draft_id):
        """
        단순 텍스트 수정
        """
        draft = Draft.objects.get(id=draft_id)
        fixed_draft = DraftTextEditSz(data=request.data)
        fixed_draft.is_valid(raise_exception=True)
        fixed_draft = fixed_draft.data.get("draft")
        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"audrey_files/project/{draft.project.id}/user_instance.json",
        )
        project.user_edit_draft(draft_id = draft.id, edit_draft=fixed_draft)

        draft.draft = fixed_draft
        draft.save()

        return SuccessResponse()
    

class DalleImageView(APIView):
    
    @swagger_auto_schema(
        operation_summary="Dalle 이미지 요청",
        tags=["Draft"],
        responses={200: DalleImageSz()},
    )
    def get(self, request, draft_id):
        draft = Draft.objects.get(id=draft_id)
        images = DalleImage.objects.filter(draft = draft)
        images_sz = DalleImageSz(images, many=True)
        
        return JsonResponse(images_sz.data, safe=False)
        
    @swagger_auto_schema(
        operation_summary="Dalle 이미지 생성 요청",
        tags=["Draft"],
        responses={200: DalleImageSz()},
    )
    def post(self, request, draft_id):
        """
        Dalle 이미지를 테이블 기반으로 생성하고 이미지 링크를 반환합니다.
        """
        draft = Draft.objects.get(id=draft_id)
        image_link, image_caption = generate_image(draft.table)
        
        new_image_instance = DalleImage(draft = draft, prompt = image_caption, link = image_link)
        new_image_instance.save()
        
        dalle_sz = DalleImageSz(new_image_instance)
        return JsonResponse(dalle_sz.data)
    
    
    @swagger_auto_schema(
        operation_summary="Draft 대표이미지 선택",
        tags=["Draft"],
        request_body=ImageSelectionSz(),
        responses={200: SuccessResponseSz()},
    )
    def put(self, request, draft_id):
        draft = Draft.objects.get(id=draft_id)
        selection_sz = ImageSelectionSz(data = request.data)
        selection_sz.is_valid(raise_exception=True)
        print(selection_sz.data)
        draft.thumbnail = selection_sz.data.get("image_id")
        draft.save()
        return SuccessResponse()
        
        
        
        
        
  
def generate_image(table: str) -> str:
        max_retries = 3
        attempts = 0
        image_url = None
        while attempts < max_retries:
            try:
                image_caption = DraftsConfig.image_generation_chain.run(table=table)
                image_url = DraftsConfig.dalle.generate_image(image_caption)
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                attempts += 1
        return image_url, image_caption


from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
class DraftDownloadView(APIView):
    @swagger_auto_schema(
        operation_summary="Draft 다운로드",
        tags=["Draft"],
        responses={200: SuccessResponseSz()},
    )
    def get(self, request, draft_id):
        """
        get 요청하시면 바로 파일 다운로드 알아서 됨
        """
        draft = Draft.objects.get(id=draft_id)
        prefix = f"audrey_files/project/{draft.project.id}/drafts"
        image_flag = False
        try:
            image_instance = DalleImage.objects.get(id=draft.thumbnail)
            with open(f'{prefix}/draft_{draft_id}.md', "r") as f:
                context = f.read()
            with open(f'{prefix}/draft_{draft_id}_image.md', "w") as f:
                new = f"![]({image_instance.link})\n\n" + context
                # new = f'''<p align="center">
                # <img src="{image_instance.link}">
                # </p>\n\n''' + context
                f.write(new)
            image_flag = True
        except Exception as e:
            print(e)
        
        font = "NanumMyeongjo"
        if image_flag:
            os.system(f"pandoc {prefix}/draft_{draft_id}_image.md -o {prefix}/draft_{draft_id}.pdf --pdf-engine=xelatex --variable mainfont='{font}'")
        else:
            os.system(f"pandoc {prefix}/draft_{draft_id}.md -o {prefix}/draft_{draft_id}.pdf --pdf-engine=xelatex --variable mainfont='{font}'")
        
        file_type = "application/pdf"  # django file object에 content type 속성이 없어서 따로 저장한 필드
        fs = FileSystemStorage(prefix)
        filename = f"draft_{draft_id}.pdf"
        response = FileResponse(fs.open(filename, 'rb'), content_type=file_type)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
        # pandoc audrey_files/project/481/drafts/draft_241.md -o audrey_files/project/481/drafts/draft_241.pdf --pdf-engine=xelatex --variable mainfont='NanumMyeongjo'

class RegenerateView(APIView):
    @swagger_auto_schema(
        operation_summary="Draft 재생성",
        tags=["Draft"],
        responses={200: SuccessResponseSz()},
    )
    def put(self,request,draft_id):
        """
        현재 저장되어있는 source 기반으로 draft 재생성
        기존 드래프트가 덮어씌워집니다.
        결과는 스트리밍으로 반환됩니다.
        """
        user_files = list()
        draft = Draft.objects.get(id=draft_id)
        draft.status = 1
        draft.save()
        draft_id = draft.id
        project_instance = draft.project

        datasources = DataSource.objects.filter(project=project_instance)
        for datasource in datasources:
            user_files.append((datasource.data, datasource.data_type))

        

        suggestion_instances = DataSourceSuggestion.objects.filter(project=project_instance)
        if not (project_instance.selected_suggestion == "" or project_instance.selected_suggestion == None):
            for sel in project_instance.selected_suggestion.split("|"):
                si = suggestion_instances.get(id=int(sel))
                user_files.append((si.link, si.data_type))

        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"audrey_files/project/{project_instance.id}/user_instance.json",
        )

        project.add_files(user_files)
        project.parse_files_to_embedchain()

        result = get_draft_stream(project, draft_id, draft)

        response = StreamingHttpResponse(result, status=200, content_type="text/event-stream")
        return response

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
