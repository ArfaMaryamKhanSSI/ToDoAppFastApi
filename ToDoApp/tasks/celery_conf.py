from celery import Celery
from celery.utils.log import get_task_logger
from decouple import config

logger = get_task_logger(__name__)

app = Celery('task', broker=config("broker"),
             backend=config("backend"))

app.conf.update(CELERY_TASK_TRACK_STARTED=True)

