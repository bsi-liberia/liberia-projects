from flask import Flask
from flask_mail import Mail, Message
from maediprojects import app, mail
from maediprojects.query import activity as qactivity

def send_async_email():
    with app.app_context():
        created, updated = qactivity.get_updates()
        message_body = """Activity in the last 24 hours

%s projects created
%s projects updated""" % (len(created), len(updated))

        if len(created):
            message_body += "\n\nCreated projects\n - "
            message_body += "\n - ".join(list(map(lambda p: "%s (%s, %s)" % 
                (p.title, p.user.username, p.recipient_country.name), 
            created)))

        if len(updated):
            message_body += "\n\nUpdated projects\n - "
            message_body += "\n - ".join(list(map(lambda p: "%s (%s, %s)" % 
                (p.title, p.user.username, p.recipient_country.name), 
            updated)))

        msg = Message(
            subject = "MAEDI Base Projets - Update notification",
            recipients = app.config["MAIL_RECIPIENTS"],
            body = message_body
        )
        mail.send(msg)

send_async_email()