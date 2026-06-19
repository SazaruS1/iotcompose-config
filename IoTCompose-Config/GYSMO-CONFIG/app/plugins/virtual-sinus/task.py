import logging

import numpy as np

from core.models import Parameter, Device
from core.task import Task
from core.utils import safe_int, safe_float

import core.datastore as ds
logger = logging.getLogger(__name__)

class VirtualSinusTask(Task):

    def __init__(self, id, plugid: "Str"):
        super().__init__(id, plugid=plugid)

        self._A = None
        self._T = None

    def sync(self,params):

        # La période
#        obj = Parameter.get_or_none(plugid=self.plugid, name="period")
#        if obj is None:
#            period = 1
#            Parameter.create(plugid=self.plugid, name="period", value=period)
#        else:
        self.set_period(safe_int(params.get('pariod'),1))

        # On récupère les paramètres utiles
##        obj = Parameter.get_or_none(plugid=self.plugid, name= "A")
##        if obj is None:
#            A = 0
#            Parameter.create(plugid=self.plugid,name= "A", value=A)
#        else:
        self._A = safe_float(params.get("A"),1)

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "T")
#        if obj is None:
#            T = 60
#            Parameter.create(plugid=self.plugid,name= "T", value=T)
#        else:
#            T = safe_float(obj.value)
        self._T  = safe_float(params.get("T"),1)



    def start(self):

        json = {
            "uid": f"{self.plugid}",
            "description": f"sinus de période {self._T} et d'amplitude {self._A}",
            "unit": "-",
            "name": "sinus",

            "min_value": -1.1*self._A,
            "max_value": +1.1*self._A,
            "digits": 5,

            "period": 0,
            "min_period": 0,
            "max_period": 0,

            "validated_by": "internal",
            "active": True,

            "read_only": True,
            "virtual": True
            }



        dev = Device.get_or_none(uid=f"{self.plugid}")
        if dev is None:
            # Création
            Device.create(**json)
        else:
            # Mise à jour
            Device.update(**json).where(Device.id == dev.id).execute()

    def execute(self, time, did, force):

        # On exécute la tâche
        logger.info(f"Itération of {self.plugid} @ {time}")
        data = {
            "sinus": self._A*np.sin(2*np.pi*time.timestamp()/self._T),
        }

        ds.push(data)
