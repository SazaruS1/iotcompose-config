import datetime
import os

from flask import Blueprint, render_template, request, url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField

from core import system
from core.web import dynamic_url_for
from . import io
from .models import Rule

webapp = Blueprint('rule-engine', __name__, template_folder="views")

@webapp.route('/')
def index():
    rules = io.export_as_dict(f"{request.plugid}")
    return render_template('rule_engine/index.html',rules=rules)

class FileForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    submit = SubmitField('Submit')

@webapp.route('/load', methods=['GET', 'POST'])
def load():
    form = FileForm()

    if form.validate_on_submit():
        bytes_ =  form.file.data.read()
        src = bytes_.decode('utf-8')

#        import core.task as task_service
#        engine = task_service.find(f'{request.blueprint}-task')

        from . import io
        io.parse(src,f'{request.plugid}')
        io.dump(f'{request.plugid}')

        return redirect(dynamic_url_for(f'%.index'))

    return render_template('rule_engine/load.html',form=form)
