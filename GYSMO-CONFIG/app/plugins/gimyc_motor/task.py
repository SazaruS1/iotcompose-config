import json
import logging
#import os
import random

import numpy as np

from .mode import Mode
from core import datastore
#from core.models import Parameter, Device
from core.task import Task
from core.utils import safe_float, safe_int

logger = logging.getLogger(__name__)


class GymicPocMotorControlTask(Task):

    def __init__(self, id, plugid: str):
        super().__init__(id, plugid=plugid)

        # TODO: Déclarer les attroibuts


        self._config = None

        self._filter_regex = None

        self._axis = 0 # L'axe des miroirs par rapport à l'axe NS. (+ vers l'ouest). Angle du miroir compté dans le sens horaire (comme az)

        # Les deux clés nécessaires pour récupérer la position du Soleil
        self._az_name = ""
        self._el_name = ""

        self._emergency_name = None

        ## ON charge le JSON et on complete
        # self._geom = GymicPocMotorControlTask.load_from_json()#

    #        # On ajoute la clé <a>lpha
    #        for i in range(len(self._geom["mirrors"]["pos"])):
    #            self._geom["mirrors"]["pos"][i]["a"] = 0

    #        # ON ajoute la dernière version des données
    #        self._geom["ts"] = None
    #        self._geom["sun"] = {"az": None, "el": None}

    def get_config(self):
        return self._config

    def sync(self, params):

        # On récupère la regex de selection des DEVICE (nom)
        # obj = Parameter.get_or_none(plugid=self.plugid, name="regex")
        # if obj is None:
        #     regex = ".*"
        #     Parameter.create(plugid=self.plugid, name="regex", value=regex)
        # else:
        #     regex = str(obj.value)
        self._filter_regex = params.get("prefix-regex",".*")

        self._emergency_name = params.get("emergency","")

        if len(self._emergency_name) >  0:
            self.add_regex(self._emergency_name) # Déclenchement sur regex

        # On récupère la période
        # obj = Parameter.get_or_none(plugid=self.plugid, name="period")
        # if obj is None:
        #     period = 10
        #     Parameter.create(plugid=self.plugid, name="period", value=period)
        # else:
        #     period = safe_int(obj.value, 1)
        # self.set_period(period)
        self.set_period(safe_int(params.get("period"),10))

        # On récupère la liste et la configuration des moteurs
        #obj = Parameter.get_or_none(plugid=self.plugid, name="config")
        #if obj is None:
        #    self._config = dict()  # Aucun moteurs pour le moment
        #else:
        #    self._config = json.loads(obj.value)
        self._config = json.loads(params.get("config","{}"))

        #obj = Parameter.get_or_none(plugid=self.plugid, name="azimut-name")
        #if obj is None:
        #    Parameter.create(plugid=self.plugid, name="azimut-name", value=self._az_name)
        #else:
        #    self._az_name = obj.value
        self._az_name = params.get("azimut-name","")

        #obj = Parameter.get_or_none(plugid=self.plugid, name="elevation-name")
        #if obj is None:
        #    Parameter.create(plugid=self.plugid, name="elevation-name", value=self._el_name)
        #else:
         #   self._el_name = obj.value
        self._el_name = params.get("elevation-name", "")

        self._axis = safe_int(params.get("axis"),0)


        logger.info(f"Configuration moteur(s) actuelle : \n{self._config}")

    def start(self):
        pass

    @property
    def filter_regex(self): return self._filter_regex
        
    def execute(self, time, did, force):

        # On exécute la tâche
        logger.info(f"Itération of GymicPocMotorControlTask {self.plugid} @ {time}")

        emergency_stop = False
        if self._emergency_name is not None:
            tmp = az = datastore.pull(self._emergency_name).get(self._emergency_name)
            emergency_stop = tmp == 1


        # On récupère la position en cours
        az = datastore.pull(self._az_name).get(self._az_name)
        el = datastore.pull(self._el_name).get(self._el_name)

        # On s'occupe de chaque moteur
        for uid, dico in self._config.items():
            # on déduit l'angle en fonction du mode 
            mode = dico.get("mode",Mode.RANDOM)
            target = dico.get("target",0)

            if az is None or el is None: # On force le mode random
                logger.warning(f"Missing sun position @ {time} -> Random")
                mode = Mode.RANDOM
            if emergency_stop: # On force le mode random
                logger.warning(f"Emergency Stop @ {time} -> Random")
                mode = Mode.RANDOM

            angle = None
            if mode == Mode.RANDOM:
                angle = random.uniform(-90, 90)
            elif mode == Mode.UP:
                angle = 0
            elif mode == Mode.DOWN:
                angle = -180
            elif mode == Mode.OFF:
                # On reprend le précédent
                angle = dico.get("command")
                angle = random.uniform(-90, 90) if angle is None else angle
            elif mode == Mode.FOLLOW:
                target = safe_float(dico.get("target"),0) # angle de référence -> pointe vers le capteur
                angle = self._get_reflect_angle(az,el,target)
            elif mode == Mode.TRANSPARENT:
                angle = self._get_transparent_angle(az,el)
            elif mode == Mode.FIXED:
                pass
            else:
                logger.warning("Impossible ici")


        # if az is None or el is None:
        #     logger.warning(f"Missing sun position @ {time}")
        #     # ON publie un ZERO pour tous les moteurs
        #     for uid in self._config.keys():
        #         # On ne publie pas directement le MQTT sur les action
        #         # TODO: peut-être écouter +/action pour traiter de la même façon que data?
        #         #mqtt.publish(f"{uid}/action", 0)
        #         datastore.push({self._config[uid]["name"]: 0})
        #     return

        

        # On calcule la hauteur apparente du Soleil dans le plan principal
       # axis = 0
       # theta_s = np.degrees(np.atan2(np.tan(np.radians(el)), np.cos(np.radians(az - axis))))

        # on  calcule pour chaque miroir
#        for uid in self._config.keys():
            # if not self._config[uid].get("active"):
            #     continue
            #target = self._config[uid]["target"]
            #angle = 0.5 * (target + theta_s)

            datastore.push({dico["name"]: angle})
            #mqtt.publish(f"{uid}/action", angle)

        # for i in range(len(self._geom["mirrors"]["pos"])):
        #
        #     # Hauteur apparente du capteur par rapport au miroir:
        #     xm = self._geom["mirrors"]["pos"][i]["x"]
        #     ym = self._geom["mirrors"]["pos"][i]["y"]
        #     theta_c = np.degrees(np.arctan2(yc-ym,xc-xm))
        #
        #     angle =90-0.5*(theta_c + theta_s)
        #
        #     # On change de signe du fait de la convention choisie...
        #     self._geom["mirrors"]["pos"][i]["a"] = - angle
        #     data[f"Miroir_{i}"] = - angle

        # Data.push(data)

    # @staticmethod
    # def load_from_json():
    #     # Obtenir le chemin absolu du répertoire contenant le fichier source
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #
    #     # Construire le chemin vers le fichier geom.json
    #     file_path = os.path.join(current_dir, 'geom.json')
    #
    #     logger.info(f"GymicPocMotorControl :: Loading {file_path}")
    #
    #     with open(file_path, 'r') as file:
    #         geom = json.load(file)
    #
    #     return geom

    # @staticmethod
    # def create_device(i,m):
    #     name = f"Miroir_{i}"
    #     logger.info(f"Create mirror device {name} if missing")
    #     dev = Device.find_by_name(name)
    #     if dev is None:
    #         dev = Device({
    #             "uid": name,
    #             "description": f"Inclinaison actionneur {i}",
    #             "unit": "°",
    #             "name": name,
    #
    #             "min_value": -90,
    #             "max_value": 90,
    #             "delta_value": 0.01,
    #
    #             "period": 0,
    #             "min_period": 0,
    #             "max_period": 0,
    #
    #             "validated_by": "internal",
    #             "active": True,
    #
    #             "read_only": False,
    #             "virtual": True
    #         })
    #         dev.save()
    #
    #     # On met à plat
    #     Data.push({name: 0})

# task = GymicPocMotorControlTask()

    def _get_reflect_angle(self,az, el, target):
        theta_s = np.degrees(
            np.atan2(
                np.sin(np.radians(el)),
                np.cos(np.radians(el))
                * np.cos(np.radians(az - self._axis))
            )
        )
        return 0.5 * (target - theta_s)
    
    def _get_transparent_angle(self, az, el):
        theta_s = np.degrees(
            np.atan2(
                np.sin(np.radians(el)),
                np.cos(np.radians(el))
                * np.cos(np.radians(az - self._axis))
            )
        )
        return ((theta_s + 90) % 180) - 90