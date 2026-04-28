import datetime

from flask import Blueprint, render_template

from core.models import Message

webapp = Blueprint("__MUST_BE_CHANGED___", __name__, template_folder="views")


@webapp.route('/')
def index():
    loglist = list(Message.select().order_by(Message.created_at.desc()).limit(10))
    return render_template("message/index.html", loglist = loglist)
