import smtplib
from email.message import EmailMessage
import os
import ssl

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
import app.crud as crud
from app.database import get_DB

logger = get_task_logger(__name__)

context = ssl.create_default_context()
sender = os.environ.get('sender')
password = os.environ.get('smtp_password')

celery = Celery('task', broker=os.environ.get("CELERY_BROKER_URL"),
                backend=os.environ.get("CELERY_RESULT_BACKEND"))

celery.conf.timezone = 'UTC'

celery.conf.beat_schedule = {
    'every-day-midnight': {
        'task': 'due today',
        'schedule': crontab(hour="0", minute="0"),
    }
}


def create_template_email(receiver, subject, message):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(
        message
    )
    return msg


@celery.task
def send_email(email, subject, message):
    msg = create_template_email(receiver=email, subject=subject, message=message)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, email, msg.as_string())
        return True


@celery.task(name="due today")
def send_tasks_due_today():
    db = next(get_DB())
    users = crud.get_all_users(db)
    for user in users:
        tasks_list = []
        due_today = crud.get_tasks_due_today(db, user_id=user.id)
        if due_today:
            tasks_list = [task.title for task in due_today]
            message = f"""
                        Hi!
                        These are your tasks due today:
                        {"     ".join(tasks_list)}
                        """
            subject = "Tasks due today"
            send_email(email=user.email, subject=subject, message=message)
