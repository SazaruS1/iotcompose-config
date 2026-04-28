import logging
import re

import numpy as np
from flask import Blueprint, request, abort, render_template, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from peewee import DoesNotExist
from wtforms import SelectMultipleField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import SubmitField
from wtforms.validators import InputRequired, NumberRange, DataRequired

from core.models import Device, Parameter
from core.web import dynamic_url_for

import json

logger = logging.getLogger(__name__)

webapp = Blueprint('__MUST_BE_CHANGED__', __name__, template_folder="views", static_folder='views/static')


#
class ConfigureForm(FlaskForm):
    # Juste pour le CRSF et le submit
    submit = SubmitField('Submit')

class AutosetForm(FlaskForm):
    height = FloatField("height")
    offset = FloatField("offset")
    step = FloatField("step")
    submit = SubmitField('Submit')


@webapp.route('/')
def index():
    # On récupère la tache
    task = get_task_or_500()

    # on récumère la configuration
    data = task.get_config() or {}

    # On complète avec la position courante (si dispo)
    for d in data.keys():
        device = Device.get(Device.uid == d)
        data[d]["angle"] = device.last_data_value if device.last_data_value is not None else "??"

    # trie selon name
    data = dict(sorted(data.items(), key=lambda item: item[1]['name']))

    return render_template('gimyc_poc/index.html', data=data)


@webapp.route('/configure', methods=['GET', 'POST'])
def configure():
    # On récupère la tache
    task = get_task_or_500()

    # Création du formulaire <de base> pour gérer le CRSF
    form = ConfigureForm()

    if request.method == "POST":
        # ON récupère la liste des devices prévus
        devices_uid = request.form.getlist('selected')

        # la configuration actuelle...
        current = task.get_config()
        config = dict()  # La nouvelle configuration

        for d in devices_uid:
            if d in config:
                # Le device est déjà connu -> on récupre les données existantes...
                config[d] = current[d]
            else:
                # Le device n'est pas connu -> on ajoute
                dev = Device.get(Device.uid == d)
                if dev is None:
                    logger.error(f"Device with uid={d} not found")
                    continue
                config[d] = {"name": dev.name, "target": 0, "active":False}

        # On sauvegarde
        Parameter.set(plugid=f"{request.plugid}", name="config", value=json.dumps(config))
        task.sync(Parameter.getDict(request.plugid))

        return redirect(dynamic_url_for('%.index'))

    # On récumère la liste des actionneurs... (ici tous les devices)
#    devices = Device.select().where( (Device.active == 1) &
 #       (Device.name.regexp(task.get_name_regex()))).dicts()
    devices = Device.select().where(Device.active == 1).dicts()

    choices = []
    for d in devices:
        if re.match(task.regex, d["name"]):
            choices.append((d["uid"], d["name"]))


    return render_template('gimyc_poc/configure.html', form=form, list=choices)


def get_task_or_500():
    import core.task as task_service
    task = task_service.find(f"{request.blueprint}-task")
    if task is None:
        logger.error(f"Unable to find {request.blueprint}-task")
        abort(500)
    return task


@webapp.route('/echo', methods=['POST'])
def echo():
    # Récupérer les données JSON envoyées dans la requête
    data = request.get_json()

    # Si les données ne sont pas valides, renvoyer une erreur
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Retourner les mêmes données reçues dans la réponse
    return jsonify(data)


@webapp.route('/set-angle', methods=['POST'])
def set_angle():
    task = get_task_or_500()
    data = request.get_json()

    # On récupère les informations
    uid = data["uid"]
    try:
        angle = float(data["angle"])
    except ValueError:
        return {}, 400

    # On vérifie que l'UID est bien dans les actionneurs référencés
    config = task.get_config()
    if uid not in config:
        return {}, 400

    # On met à jour l'actionneur
    try:
        dev = Device.get(Device.uid == uid)

        from core import datastore
        datastore.push({dev.name: angle})

    except DoesNotExist:
        return {}, 400

    return {}, 200 # Fin normale

@webapp.route('/set-state', methods=['POST'])
def set_state():
    task = get_task_or_500()
    data = request.get_json()

    # On récupère les informations
    uid = data["uid"]
    state = data["state"]

    # On vérifie que l'UID est bien dans les actionneurs référencés
    config = task.get_config()
    if uid not in config:
        return {}, 400

        # On met à jour la référence dans la CONFIG
    config[uid]["active"] = state
    Parameter.set(plugid=f"{request.plugid}", name="config", value=json.dumps(config))
    task.sync(Parameter.getDict(request.plugid))

    return {}, 200 # Fin normale



@webapp.route('/set-target', methods=['POST'])
def set_target():
    task = get_task_or_500()
    data = request.get_json()

    # On récupère les informations
    uid = data["uid"]
    try:
        angle = float(data["angle"])
    except ValueError:
        return {}, 400

    # On vérifie que l'UID est bien dans les actionneurs référencés
    config = task.get_config()
    if uid not in config:
        return {}, 400

    # On met à jour la référence dans la CONFIG
    config[uid]["target"] = angle
    Parameter.set(plugid=f"{request.plugid}", name="config", value=json.dumps(config))
    task.sync(Parameter.getDict(request.plugid))

    return {}, 200

@webapp.route('/set-vertical', methods=['POST'])
def set_vertical():
    task = get_task_or_500()
    data = request.get_json()

    # On récupère les informations
    uid = data["uid"]
    try:
        angle = float(data["angle"])
    except ValueError:
        return {}, 400

    # On vérifie que l'UID est bien dans les actionneurs référencés
    config = task.get_config()
    if uid not in config:
        return {}, 400

    # Expédition du topic
    from core.mqtt import publish
    publish(f"{uid}/command","SET_ZERO")

    return {}, 200

@webapp.route('/trig')
def trig():
    import core.task as task_service
    task = task_service.find(f"{request.blueprint}-task")
    if task is None:
        logger.error(f"Unable to find {request.blueprint}-task")
        abort(500)

    task.fire()
    return redirect(url_for(f'{request.blueprint}.index'))
    # return render_template('gimyc_poc/index.html', last = task._last_trigger)


@webapp.route('/autoset', methods=['GET', 'POST'])
def autoset():
    task = get_task_or_500()


    form = AutosetForm()

    if request.method == "POST":
        # ON récupère la liste des devices prévus
        height = request.form.get('height', type=float)
        offset = request.form.get('offset', type=float)
        step = request.form.get('step', type=float)

        if height is None or offset is None or step is None:
            return render_template('gimyc_poc/autoset.html', form=form)

        # la configuration actuelle...
        config = task.get_config()

        # On trie dans l'ordre des nom
        #TODO: Ajouter un champs ORDER
        config = dict(sorted(config.items(), key=lambda item: item[1]['name']))

        for i, key in enumerate(config): # Pour chaque moteur
            config[key]['target'] = -np.degrees(np.atan2(i*step-offset, height))


        # On sauvegarde
        Parameter.set(plugid=f"{request.plugid}", name="config", value=json.dumps(config))
        task.sync(Parameter.getDict(request.plugid))

        #
        # for d in devices_uid:
        #     if d in config:
        #         # Le device est déjà connu -> on récupre les données existantes...
        #         config[d] = current[d]
        #     else:
        #         # Le device n'est pas connu -> on ajoute
        #         dev = Device.get(Device.uid == d)
        #         if dev is None:
        #             logger.error(f"Device with uid={d} not found")
        #             continue
        #         config[d] = {"name": dev.name, "target": 0, "active": False}
        #
        # # On sauvegarde
        # Parameter.set(plugid=f"{request.plugid}", name="config", value=json.dumps(config))
        # task.sync(Parameter.getDict(request.plugid))

        return redirect(dynamic_url_for('%.index'))

    # On récumère la liste des actionneurs... (ici tous les devices)
    #    devices = Device.select().where( (Device.active == 1) &
    #       (Device.name.regexp(task.get_name_regex()))).dicts()
    #devices = Device.select().where(Device.active == 1).dicts()

    # choices = []
    # for d in devices:
    #     if re.match(task.regex, d["name"]):
    #         choices.append((d["uid"], d["name"]))

    return render_template('gimyc_poc/autoset.html', form=form)
