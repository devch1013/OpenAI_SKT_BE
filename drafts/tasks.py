from celery import shared_task
import time
from .models import *
import asyncio


@shared_task
def add(x, y):
    asyncio.run(aaa())
    pj = AiDraftModification(query_text="asdasdasds123sdadssads")
    pj.save()
    print("dhehehehehehehehehehhehehehehe")
    return x + y


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
