from decouple import config
import smtplib
from email.message import EmailMessage
import ssl

context = ssl.create_default_context()
sender = config('sender')
password = config('password')


def create_template_email(receiver, link):
    """
    creates message for email
    :param receiver:
    :param link:
    :return:
    """
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


def send_verification_email(token, user_email):
    """
    sends email to user email
    :param token:
    :param user_email:
    :return:
    """
    msg = create_template_email(receiver=user_email, link=token)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, user_email, msg.as_string())
