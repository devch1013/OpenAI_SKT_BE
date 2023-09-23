from celery import shared_task
import time
from .models import *
import asyncio
from .apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi

# from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async


@shared_task
def add(x, y):
    asyncio.run(aaa())
    pj = AiDraftModification(query_text="asdasdasds123sdadssads")
    pj.save()
    print("dhehehehehehehehehehhehehehehe")
    return x + y

@shared_task
def celery_test():
    print("cleery!")
    return 123

@shared_task
def get_suggestion(project_id, purpose, table):
    print("celery task")
    project_instance = Project.objects.get(id=project_id)
    asyncio.run(async_suggestion_task(project_instance, purpose, table))
    print("task_completed")
    project_instance.suggestion_flag = True
    project_instance.save()
    return True


async def async_suggestion_task(project_instance, purpose, table):
    project = ProjectAi.load(
        project_id=project_instance.id,
        **(DraftsConfig.instances),
        purpose=purpose,
        table=table,
    )

    keywords = project.get_keywords()
    files = await project.async_search_keywords()
    source_template = {
        "kostat": "kostat",
        "youtube": "youtube",
        "google_search": "google",
        "naver_search": "naver",
        "gallup": "gallup",
    }
    # for api_type, infos in files.items():
    #     for info in infos:
    #         try:
    #             print(info)
    #             suggestion = DataSourceSuggestion()
    #             suggestion.project = project_instance
    #             suggestion.title = info["title"]
    #             suggestion.source = source_template[api_type]
    #             suggestion.description = info["description"]
    #             suggestion.data_type = info["data_type"]
    #             suggestion.link = info["data_path"]
    #             await database_sync_to_async(suggestion.save)()
    #         except Exception as e:
    #             print(e)
                
    for keyword, infos in files.items():
        for api_type, info in infos.items():
            for data in info:
                try:
                    # print(data)
                    suggestion = DataSourceSuggestion()
                    suggestion.project = project_instance
                    suggestion.title = data["title"]
                    suggestion.source = source_template[api_type]
                    suggestion.description = data["description"]
                    suggestion.data_type = data["data_type"]
                    suggestion.link = data["data_path"]
                    suggestion.keyword = keyword
                    await database_sync_to_async(suggestion.save)()
                except Exception as e:
                    print(e)
    project_instance.keywords = "|".join(keywords)
    await database_sync_to_async(project_instance.save)()
    # print(files)
    project.save()
    return files


@shared_task
def write_first_draft(project_id, draft_id, user_files):
    project_instance = Project.objects.get(id=project_id)

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
    project = ProjectAi.load(
        project_id=project_id,
        **(DraftsConfig.instances),
        purpose=project_instance.purpose,
        table=project_instance.table,
        keywords=project_instance.keywords.split("|"),
        files=suggestion_file_dict,
    )

    project.add_files(user_files)
    database = project.parse_files_to_embedchain()
    draft = project.get_draft(draft_id=draft_id)
    project.save()

    draft_instance = Draft.objects.get(id=draft_id)
    draft_instance.table = project_instance.table
    draft_instance.draft = draft
    draft_instance.status = 2
    draft_instance.name = "Draft 1"
    draft_instance.save()
    print(draft)


async def aaa():
    time.sleep(3)
    print("sleep!!!")
    return


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)
