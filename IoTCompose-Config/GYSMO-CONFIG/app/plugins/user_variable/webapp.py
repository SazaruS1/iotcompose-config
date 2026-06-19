import logging
import os
import sys
import datetime

from flask import render_template, Blueprint, redirect, abort, flash, request, url_for
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField, BooleanField
from wtforms.fields.numeric import FloatField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets.core import CheckboxInput

from core.models import Device, Record
from core.web import dynamic_url_for

from core.mqtt import publish as mqtt_publish  # en haut du fichier

logger = logging.getLogger(__name__)

from .helpers import create_user_var

webapp = Blueprint('-', __name__, template_folder="views")


@webapp.route('/')
def index():
    rep = list(
        Device.select().where(
#            (Device.virtual == True) &
            (Device.active == True) &
            (Device.read_only == False)
        )
    )

    return render_template("user_variable/index.html", vars=rep)


class CreateForm(FlaskForm):
    uid = StringField("uid", validators=[DataRequired()])
    name = StringField("name", validators=[DataRequired()])
    unit = StringField("unit")
    value = FloatField("value", validators=[InputRequired()])
    min_value = FloatField("min_value")
    max_value = FloatField("max_value")
    description = StringField("description")

    submit = SubmitField('Valider')


@webapp.route('/create', methods=['GET', 'POST'])
def create():
    form = CreateForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Récupération des données du formulaire
            uid = form.uid.data
            name = form.name.data
            unit = form.unit.data
            value = form.value.data
            min_value = form.min_value.data
            max_value = form.max_value.data
            description = form.description.data

            device = create_user_var(uid, name, description, unit, min_value, max_value)

            logger.info(f"Creation of user variable {device}")
            print(f">>>>>>>>>>>Creation of user variable {device}")

            if device is not None:
                ts = datetime.datetime.now()
                device.last_data_value = value
                device.last_data_at = ts
                device.save()

                Record.create(device=device, value=value, ts=ts, action=True)

                flash("Device créé avec succès !", "success")
                return redirect(dynamic_url_for(f'%.index'))  # rediriger pour éviter le repost

            else:
                flash("Création impossible : UID ou nom existant", "error")

        else:
            flash("Erreur de validation du formulaire", "error")

    return render_template("user_variable/create.html", form=form)


class EditForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    unit = StringField("unit")
    min_value = FloatField("min_value")
    max_value = FloatField("max_value")
    description = StringField("description")

    submit = SubmitField('Valider')


@webapp.route('/edit/<string:uid>', methods=['GET', 'POST'])
def edit(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    form = EditForm(obj=dev)
    if request.method == "POST":
        if form.validate_on_submit():
            # Récupération des données du formulaire
            name = form.name.data
            unit = form.unit.data
            min_value = form.min_value.data
            max_value = form.max_value.data
            description = form.description.data

            dev.name = name
            dev.unit = unit
            dev.min_value = min_value
            dev.max_value = max_value
            dev.description = description
            dev.save()

            logger.info(f"Update of user variable {dev}")
            print(f">>>>>>>>>>>Creation of user variable {dev}")

            flash("Variable modifiée avec succès !", "success")
            return redirect(dynamic_url_for(f'%.index'))  # rediriger pour éviter le repost


        else:
            flash("Erreur de validation du formulaire", "error")

    return render_template("user_variable/edit.html", form=form)


class SetForm(FlaskForm):
    value = FloatField("value")
    submit = SubmitField('Valider')


@webapp.route('/set/<string:uid>', methods=['GET', 'POST'])
def set(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    form = SetForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Récupération des données du formulaire
            value = form.value.data

            # Validation min/max
            if value < dev.min_value or value > dev.max_value:
                flash(f"Valeur hors limites [{dev.min_value}, {dev.max_value}]", "error")
                return render_template("user_variable/set.html", form=form, name=dev.name, unit=dev.unit)

            # Arrondi selon le nombre de digits
            if dev.digits == 0:
                rounded = int(round(value, 0))
            else:
                rounded = round(value, dev.digits)

            
            if rounded != value:
                flash(f"Valeur arrondie de {value} à {rounded}", "warning")
                value = rounded


            ts = datetime.datetime.now()
            if dev.virtual:
                dev.last_data_value = value
                dev.last_data_at = ts
                dev.save()
                Record.create(device=dev, value=value, ts=ts, action=False)
            else:
                # Actionneur : on sauvegarde ET on publie la commande MQTT
                dev.last_action_value = value
                dev.last_action_at = ts
                dev.save()
                Record.create(device=dev, value=value, ts=ts, action=True)
                mqtt_publish(f"{dev.uid}/action", value)   # ← commande MQTT vers l'actionneur
            logger.info(f"Set value of user variable {dev}")

            flash(f"Valeur de la variable {dev.name} modifiée avec succès !", "success")
            return redirect(dynamic_url_for(f'%.index'))  # rediriger pour éviter le repost

        else:
            flash("Erreur de validation du formulaire", "error")

    return render_template("user_variable/set.html", form=form, name=dev.name, unit=dev.unit)


@webapp.route('/delete/<string:uid>')
def delete(uid):
    dev = Device.get_or_none(uid=uid)

    if dev is None:
        abort(404)

    dev.delete_instance()
    return redirect(dynamic_url_for('%.index'))
