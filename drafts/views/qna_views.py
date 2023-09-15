from django.shortcuts import render
from rest_framework.views import APIView
from django.http.response import StreamingHttpResponse
from django.http import JsonResponse
from main.responses.success_responses import SuccessResponse
from ..models import *
from ..serializers.project_sz import *
from ..serializers.draft_sz import *
from ..serializers.qna_sz import *
from ..tasks import get_suggestion, write_first_draft
from ..apps import DraftsConfig
from ..utils.streaming_queue import StreamingQueue
from writer.openai_skt.modules import Project as ProjectAi
from drf_yasg.utils import swagger_auto_schema
import pickle
from django.db.models import Q
import threading
from time import time


class QnAViews(APIView):
    def get(self, request, project_id):
        project_db = Project.objects.get(id=project_id)
        conversation_q = Conversation.objects.filter(project=project_db).order_by("-timestamp")
        if not conversation_q.exists():
            return JsonResponse({})
        last_conversation = conversation_q[0]
        if last_conversation.deleted == True:
            return JsonResponse({})
        conversation_history = list()
        utterances = Utterance.objects.filter(conversation = last_conversation).order_by("timestamp")
        for ut in utterances:
            conversation_history.append({"user":ut.user_side, "model": ut.ai_side})
            
        return JsonResponse({"conversation": conversation_history})
        
        
        
        
        
    @swagger_auto_schema(
        operation_summary="QnA 질문 요청",
        tags=["QnA"],
        request_body=QnARequestSz(),
        responses={}
    )
    def post(self, request, project_id):
        question = QnARequestSz(data=request.data)
        question.is_valid(raise_exception=True)
        question = question.validated_data.get("question")
        project_db = Project.objects.get(id=project_id)
        conversation_q = Conversation.objects.filter(project=project_db).order_by("-timestamp")
        if (not conversation_q.exists()) or (conversation_q[0].deleted == True):
            conversation = Conversation(project=project_db)
            conversation.save()
        else:
            conversation = conversation_q.order_by("-timestamp")[0]
        utterance = Utterance.objects.filter(conversation=conversation).order_by("timestamp")
        qna_history = list()
        if len(utterance) > 2:
            utterance = utterance[:2]
        for ut in utterance:
            qna_history.append([ut.user_side, ut.ai_side])

        project = ProjectAi.load_from_file(
            **(DraftsConfig.instances),
            user_instance_path=f"audrey_files/project/{project_db.id}/user_instance.json",
        )

        answer = qna_interceptor(
            conversation=conversation,
            question=question,
            qna_history=qna_history,
            project=project
        )
        response = StreamingHttpResponse(answer, status=200, content_type="text/event-stream")
        return response
    
    def delete(self, request, project_id):
        project_db = Project.objects.get(id=project_id)
        conversation_q = Conversation.objects.filter(project=project_db).order_by("-timestamp")
        if not conversation_q.exists():
            return SuccessResponse()
        last_conversation = conversation_q[0]
        if last_conversation.deleted == True:
            return SuccessResponse()
        last_conversation.deleted = True
        last_conversation.save()
        return SuccessResponse()
        


def qna_interceptor(conversation, question, qna_history, project):
    new_utterance = Utterance(conversation=conversation)
    new_utterance.user_side = question
    streaming_queue = StreamingQueue()
    content = ""

    def chat_task():
        project.get_qna_answer(
            question=question,
            qna_history=qna_history,
            queue=streaming_queue,
        )
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

    time_to_response = int((time() - start) * 1000)
    new_utterance.ai_side = content
    new_utterance.time_to_response = time_to_response
    new_utterance.save()
