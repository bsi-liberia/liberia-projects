from flask import request, current_app

from flask_mail import Message
from maediprojects.extensions import mail


def send_async_email(message_recipient, message_subject, message_body):
    with current_app.app_context():
        msg = Message(
            subject = message_subject,
            recipients = [message_recipient],
            body = message_body
        )
        mail.send(msg)
