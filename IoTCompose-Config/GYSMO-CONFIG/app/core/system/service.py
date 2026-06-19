# En charge de gérer globalement la plateforme
import importlib
import inspect
import logging
import os
import subprocess
import sys

import yaml

import core.mqtt as mqtt_service
import core.plugin as plugin_service
import core.web as web_service
from core.models import Parameter
from core.plugin import Plugin


logger = logging.getLogger(__name__)

class SystemException(Exception):
    pass


#def add_plugin(plugin):

    #plugin_service.add(plugin)


def start(prod = False):
    mqtt_service.start()
    plugin_service.start()

def stop():

    mqtt_service.stop()
    plugin_service.stop()
    web_service.stop()

def restart():
    logger.info("Restarting...")
    subprocess.Popen("./gysmo.sh RESTART", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _get_plugin_classes(module):
    # Obtenir la liste des classes définies dans le module
    classes = inspect.getmembers(module, inspect.isclass)

    # Filtrer pour garder uniquement les classes définies dans ce module qui héritent de Plugin
    classes_defined_in_module = [
        cls for name, cls in classes
        if cls.__module__ == module.__name__ and issubclass(cls, Plugin)
    ]

    # Afficher la liste des classes définies qui héritent de Plugin
    for cls in classes_defined_in_module:
        print(f"Classe : {cls.__name__}")

    return classes_defined_in_module

def _load(uid, data):

#    print(f"On s'occupe de {uid}")
#    print(f"|  classe = {data['class']}")
#    print(f"|  prefix = {data['prefix']}")
#    print(f"|  menu = {data.get("menu")}")

    try:
        module = importlib.import_module(data['class'])
    except ModuleNotFoundError as e:
        raise SystemException(f"Plugin {data['class']} not found")


    # On récupère les classes de type Plingin qui sont définies dans les package
    Classes_ = _get_plugin_classes(module)

    if Classes_ is None:
        raise SystemException(f"Plugin {data['class']} not found")
    elif len(Classes_) > 1:
        raise SystemException(f"Ambiguous reference for plugin {data['class']}")


    #if not hasattr(module, Classes_):
    #    raise SystemException(f"Plugin defined in class {datastore['class']} not found")


    #Classes_ = getattr(module, classes[0])
    instance = Classes_[0](uid, prefix=data['prefix'],menu_name=data.get("menu"))

    return instance



def load_plugins(filename):

    print(f"OUVERTURE DE {filename}")
    try:
        with open(filename, 'r') as file:
            items = yaml.safe_load(file)

            for uid, data in items.items():
                plugin = _load(uid,data)

                plugin_service.add(plugin)

                # Récupération des informations de configuration initiale [si n'exite pas en base]
                if 'params' in data:
                    for k, v in data['params'].items():
                        para = Parameter.get_or_none(plugid=uid, name=k)
                        if para is None:
                            Parameter.create(plugid=uid, name=k, value=v)
                            logger.info(f"Adding parameter {para}")

    except FileNotFoundError:
        raise SystemException(f"Plugins descrption file '{filename}' does not exist.")
    except IOError:
        raise SystemException(f"An I/O error occurred while trying to read the file '{filename}'.")
#    except Exception as e:
#        raise SystemException(f"An unexpected error occurred: {e}")

