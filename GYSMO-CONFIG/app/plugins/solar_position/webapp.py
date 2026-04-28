import datetime
import logging

from flask import Blueprint, render_template, redirect, url_for, request, abort

from flask_wtf import FlaskForm
from wtforms.fields.numeric import DecimalField, FloatField
from wtforms.fields.simple import SubmitField
from wtforms.validators import InputRequired, NumberRange

from core.models import Parameter

logger = logging.getLogger(__name__)

webapp = Blueprint('__MUST_BE_CHANGED__', __name__, template_folder="views")


class ConfigureForm(FlaskForm):
    longitude = FloatField(validators=[InputRequired(), NumberRange(min=-180, max=180, message=None)])
    latitude = FloatField(validators=[InputRequired(), NumberRange(min=-90, max=90, message=None)])
    submit = SubmitField('Submit')

@webapp.route('/')
def index():
    # je récupère la date de dernère exécution de la tâche
    import core.task as task_service
    task = task_service.find(f"{request.blueprint}-task")
    if task is None:
        logger.error(f"Unable to find {request.blueprint}-task")
        abort(500)

    params = {
        "last" : task.last_trig,
        "lon" : task.longitude,
        "lat": task.latitude,
        "last_ts": task._last_ts,
        "last_az": task._last_az,
       "last_el": task._last_el,
    }

    return render_template('solar_position/index.html', **params)

@webapp.route('/configure', methods=['GET', 'POST'])
def load():
    form = ConfigureForm()

    if form.validate_on_submit():
        longitude = form.longitude.data
        latitude = form.latitude.data

        Parameter.set(plugid=request.blueprint, name="latitude",value=latitude)
        Parameter.set(plugid=request.blueprint, name="longitude",value=longitude)

        import core.task as task_service
        task_service.sync(f"{request.blueprint}-task")

        return redirect(url_for(f'{request.blueprint}.index'))

    return render_template('solar_position/configure.html', form=form)



@webapp.route('/trig')
def trig():
    import core.task as task_service
    task = task_service.find(f"{request.blueprint}-task")
    if task is None:
        logger.error(f"Unable to find {request.blueprint}-task")
        abort(500)

    task.fire()
    return redirect(url_for(f'{request.blueprint}.index'))
    #return render_template('gimyc_poc/index.html', last = task._last_trigger)

