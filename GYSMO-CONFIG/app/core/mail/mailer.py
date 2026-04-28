# -*- coding: utf-8 -*-
import datetime
import logging
import os

from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.utils import as_bool, safe_int

logger = logging.getLogger(__name__)
current_directory = os.path.dirname(__file__)
template_dir = os.path.join(current_directory, 'templates')
template_env = Environment(loader=FileSystemLoader(template_dir))

# Nom du fichier template
template_file = "mail.html"
template = template_env.get_template(template_file)


# #####################################################
# Configuration du mailer
# #####################################################

# =============================================================================================================
# Envoi d'un mail
# =============================================================================================================

def send(message):
    # Variables pour le template
    global template

    # Rendre le template avec les variables
    sender = os.environ["MAIL_SENDER"]
    recipient = os.environ["MAIL_RECIPIENTS"]
    subject = os.environ["MAIL_SUBJECT"]

    email_body = template.render(subject=subject, message=message, ts=datetime.datetime.now())


    # Créer l'objet MIMEMultipart
    msg = MIMEMultipart('alternative')
    msg.attach(MIMEText(message.encode("utf-8"), 'plain', 'utf-8'))
    msg.attach(MIMEText(email_body, 'html', 'utf-8'))
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    #msg['Content-Type'] = 'text/plain'; charset=' + codage


    # Envoyer l'e-mail
    try:
        # Connexion au serveur SMTP (par exemple Gmail)
        server = smtplib.SMTP(os.environ["MAIL_SERVER"], safe_int(os.environ["MAIL_PORT"]))
        if as_bool(os.environ["MAIL_USE_TLS"]):
            server.starttls()
        server.login(os.environ["MAIL_USERNAME"], os.environ["MAIL_PASSWORD"])
        server.sendmail(sender, recipient.split(","), msg.as_bytes())
        server.quit()
        logger.info(f"Email sent to {sender}")
    except Exception as e:
        logger.warning(f"Error sending email to {recipient}: {e}")

