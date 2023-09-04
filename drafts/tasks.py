from celery import shared_task
import time
from .models import *
import asyncio
from .apps import DraftsConfig
from writer.openai_skt.modules import Project as ProjectAi

from asgiref.sync import sync_to_async


@shared_task
def add(x, y):
    asyncio.run(aaa())
    pj = AiDraftModification(query_text="asdasdasds123sdadssads")
    pj.save()
    print("dhehehehehehehehehehhehehehehe")
    return x + y


@shared_task
def get_suggestion(project_id, purpose, table):
    # print("in celery task",kwargs)
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
    }
    for api_type, infos in files.items():
        for info in infos:
            suggestion = DataSourceSuggestion()
            suggestion.project = project_instance
            suggestion.title = info["title"]
            suggestion.source = source_template[api_type]
            suggestion.description = info["description"]
            suggestion.data_type = info["data_type"]
            suggestion.link = info["data_path"]
            await sync_to_async(suggestion.save)()
    project_instance.keywords = "|".join(keywords)
    await sync_to_async(project_instance.save)()
    # print(files)
    return files


@shared_task
def write_first_draft(project_id, draft_id, user_files):
    project_instance = Project.objects.get(id=project_id)

    suggestion_instances = DataSourceSuggestion.objects.filter(project=project_instance)
    suggestion_file_dict = dict()
    for sel in project_instance.selected_suggestion.split("|"):
        suggestion_file_dict[sel] = list()
        for file in suggestion_instances.filter(source=sel):
            suggestion_file_dict[sel].append({"data_path": file.link, "data_type": file.data_type})
    print(suggestion_file_dict)
    project = ProjectAi.load(
        project_id=project_id,
        **(DraftsConfig.instances),
        purpose=project_instance.purpose,
        table=project_instance.table,
        keywords=project_instance.keywords.split("|"),
        files={"dummy": suggestion_file_dict},
    )
    project.add_files(user_files)
    database = project.parse_files_to_embedchain()
    draft = project.get_draft()
    project.save_instance()

    draft_instance = Draft.objects.get(id=draft_id)
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
