import datetime

from flask import Blueprint, render_template, abort, redirect
from flask_wtf import FlaskForm
from peewee import IntegrityError
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from core.models import Device
from core.web.service import dynamic_url_for

webapp = Blueprint('__MUST_BE_CHANGED__', __name__, template_folder="views")


@webapp.route('/')
def index():
    knowns = list(Device.select().where(Device.name.is_null(False)).order_by(Device.name).dicts())
    unknowns = list(Device.select().where(Device.name.is_null()).order_by(Device.name).dicts())

    return render_template("device/index.html", knowns=knowns, unknowns=unknowns)


@webapp.route('/state/<string:uid>/<int:state>')
def state(uid, state):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    if dev.name is None:
        abort(406)

    dev.active = bool(state)
    dev.save()
    return redirect(dynamic_url_for('%.index'))


@webapp.route('/delete/<string:uid>')
def delete(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    dev.delete_instance()
    return redirect(dynamic_url_for('%.index'))

@webapp.route('/invalidate/<string:uid>')
def invalidate(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    dev.name = None
    dev.active = False
    dev.save()


    return redirect(dynamic_url_for('%.index'))


class NameForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(2, 40)])
    submit = SubmitField('Submit')


@webapp.route('/validate/<string:uid>', methods=['GET', 'POST'])
def validate(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    if dev.name is not None:
        abort(406)

    form = NameForm()

    message = None
    if form.validate_on_submit():
        name = form.name.data
        dev.name = name
        dev.active = True
        try:
            dev.save()
        except IntegrityError:# Problème de duplication
            message = "Le nom existe déjà"
            return render_template('device/validate.html', form=form, device=dev, message=message)

        # On est tout bon
        return redirect(dynamic_url_for('%.index'))
    else:
        return render_template('device/validate.html', form=form, device=dev, message=message)
