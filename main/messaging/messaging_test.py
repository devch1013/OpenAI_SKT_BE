from main.messaging.celery_task import add


if __name__ == "__main__":
    add.delay(1, 3)
