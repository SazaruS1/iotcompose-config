import logging
import os

from flask import render_template, Blueprint, request
from flask_wtf import csrf

from core.models import Parameter

logger = logging.getLogger(__name__)

webapp = Blueprint('-', __name__, template_folder="views")


@webapp.route('/')
def index():
    import core.task as task

    # On construit un dictionnaire qui contient en clé
    mqtt = os.environ["MQTT_BROKER"]

    return render_template("system/index.html", tasks=task.task_list_with_parameter(),mqtt=mqtt, pid=os.getpid())


@webapp.route('/restart')
def restart():

    from core import system
    system.restart()
    return render_template("system/restart.html")


@webapp.route('/trig', methods=["POST"])
def trig():
    import core.task as task

    data = request.get_json()
    taskid = data["taskid"]

    task.force(taskid)

    return {}, 200


@webapp.route('/sync', methods=["POST"])
def sync():
    import core.task as taskservice

    data = request.get_json()
    taskid = data["taskid"]

    taskservice.sync(taskid)

    return {}, 200
    # return redirect(dynamic_url_for('%.index'))
    # return render_template("system/index.html", tasks = task.task_list())


@webapp.route('/change-parameter', methods=['POST'])
def change_parameter():
    # On récumère les données transmises
    data = request.get_json()
    plugid = data["plugid"]
    name = data["name"]
    value = data["value"]

    # On récupère le paramètre correspondant
    param = Parameter.select().where((Parameter.plugid == plugid) & (Parameter.name == name)).get_or_none()
    if param is None:
        logger.warning(f"Trying to modify {name} parameter of {plugid} plugin")
        return {}, 400

    param.value = value
    param.save()

    return {}, 200

@webapp.route('/delete-parameter', methods=['POST'])
def delete_parameter():
    # On récumère les données transmises
    data = request.get_json()
    plugid = data["plugid"]
    name = data["name"]

    # On récupère le paramètre correspondant
    param = Parameter.select().where((Parameter.plugid == plugid) and (Parameter.name == name)).get_or_none()
    if param is None:
        logger.warning(f"Trying to delete {name} parameter of {plugid} plugin")
        return {}, 400

    param.delete_instance()

    return {}, 200
