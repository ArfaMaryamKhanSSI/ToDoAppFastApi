import smtplib
from email.message import EmailMessage
import os
import ssl
from celery.utils.log import get_task_logger
from celery import shared_task
logger = get_task_logger(__name__)

context = ssl.create_default_context()
sender = os.environ.get('sender')
password = os.environ.get('smtp_password')


def create_template_email(receiver, link):
    msg = EmailMessage()
    msg['Subject'] = "Verify your Account"
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(
        f"""
        Please click this link to verify your account.
        {link}
        """
    )
    return msg


@shared_task
def send_verification_email(token, user_email):
    msg = create_template_email(receiver=user_email, link=token)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, user_email, msg.as_string())
        return True

