import datetime

from flask import Blueprint, render_template, redirect, url_for, flash

from core.models import Message

webapp = Blueprint("__MUST_BE_CHANGED___", __name__, template_folder="views")


@webapp.route('/')
def index():
    loglist = list(Message.select().order_by(Message.created_at.desc()).limit(10))
    return render_template("message/index.html", loglist=loglist)


@webapp.route('/clear')
def clear():
    query = Message.delete().where(
        (Message.validated_at.is_null(False)) |  # acquitté
        (Message.must_validate == False)          # pas besoin d'acquittement
    )
    count = query.execute()
    flash(f"{count} message(s) supprimé(s)", "success")
    return redirect(url_for(f'{webapp.name}.index'))
