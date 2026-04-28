import logging
from email.policy import default

import numpy as np
import suncalc

import core.datastore as ds


from core.models import Parameter, Device, Record
from core.task import Task
from core.utils import safe_int, safe_float

logger = logging.getLogger(__name__)


class SolarPositionTask(Task):

    def __init__(self, id, plugid: "Str"):
        super().__init__(id, plugid=plugid)
        self._longitude = None
        self._latitude = None

        self._last_ts = None
        self._last_az = None
        self._last_el = None

        # identifiants
        self._az_uid = f"{plugid}_az"
        self._el_uid = f"{plugid}_el"
        self._az_name = f"{plugid}_az"
        self._el_name = f"{plugid}_el"


    def sync(self, params):
        # On récupère les paramètres utiles
#        obj = Parameter.get_or_none(plugid=self.plugid, name= "period")
#        if obj is None:
#            period = 10
#            Parameter.create(plugid=self.plugid,name= "period", value=period)
#        else:
#            period = safe_int(obj.value,10)
        self.set_period(safe_int(params.get("period"),60))


#        obj = Parameter.get_or_none(plugid=self.plugid, name= "longitude")
#        if obj is None:
#            longitude = 0
#            Parameter.create(plugid=self.plugid,name= "longitude", value=longitude)
#        else:
#            longitude = safe_float(obj.value)
        self._longitude = safe_float(params.get("longitude"),0)

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "latitude")
#        if obj is None:
#            latitude = 0
#            Parameter.create(plugid=self.plugid,name= "latitude", value=longitude)
#        else:
#            latitude = safe_float(obj.value)
        self._latitude =  safe_float(params.get("latitude"),45)

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "azimut-uid")
#        if obj is None:
#            Parameter.create(plugid=self.plugid,name= "azimut-uid", value=self._az_uid)
#        else:
#            self._az_uid = obj.value
        self._az_uid = params.get("azimut-uid", f"{self.plugid}_az")

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "elevation-uid")
#        if obj is None:
#            Parameter.create(plugid=self.plugid,name= "elevation-uid", value=self._el_uid)
#        else:
#            self._el_uid = obj.value
        self._el_uid = params.get("elevation-uid", f"{self.plugid}_el")

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "azimut-name")
#        if obj is None:
#            Parameter.create(plugid=self.plugid,name= "azimut-name", value=self._az_name)
#        else:
#            self._az_name = obj.value
        self._az_name = params.get("azimut-name", f"{self.plugid}_az")

#        obj = Parameter.get_or_none(plugid=self.plugid, name= "elevation-name")
#        if obj is None:
#            Parameter.create(plugid=self.plugid,name= "elevation-name", value=self._el_name)
#        else:
        self._el_name = params.get("elevation-name", f"{self.plugid}_el")



    @property
    def longitude(self):
        return self._longitude

    @property
    def latitude(self):
        return self._latitude

    def start(self):

        json_az = {
            "uid": self._az_uid,
            "description": "Azimut",
            "unit": "°",
            "name": self._az_name,

            "min_value": -180,
            "max_value": +180,
            "digits": 1,

            "period": 0,
            "min_period": 0,
            "max_period": 0,

            "validated_by": "internal",
            "active": True,

            "read_only": True,
            "virtual": True
            }

        json_el = {
            "uid": self._el_uid,
            "description": "Elevation",
            "unit": "°",
            "name": self._el_name,

            "min_value": -90,
            "max_value": 90,
            "digits": 1,

            "period": 0,
            "min_period": 0,
            "max_period": 0,

            "validated_by": "internal",
            "active": True,

            "read_only": True,
            "virtual": True
        }

        # On cherche si le uid existe...
        dev_az = Device.get_or_none(uid=self._az_uid)
        if dev_az is None:
            # on cherche si par hazard on a conservé le même nm
            dev_az = Device.get_or_none(name=self._az_name)
        if dev_az is None:
            # Création
            Device.create(**json_az)
        else:
            # Mise à jour
            Device.update(**json_az).where(Device.id == dev_az.id).execute()

        dev_el = Device.get_or_none(uid=self._el_uid)
        if dev_el is None:
            # on cherche si par hazard on a conservé le même nm
            dev_az = Device.get_or_none(name=self._el_name)
        if dev_el is None:
            # Création
            Device.create(**json_el)
        else:
            # Mise à jour
            Device.update(**json_el).where(Device.id == dev_el.id).execute()


    def execute(self, time, did, force):

        # On exécute la tâche
        logger.info(f"Itération of {self.plugid} @ {time}")
        try:
            pos = suncalc.get_position(time, self._longitude,self._latitude)

            az = float(np.degrees(pos["azimuth"]))
            el = float(np.degrees(pos["altitude"]))

            data = {
                self._az_name: az,
                self._el_name: el
            }

            ds.push(data)

            self._last_ts = time
            self._last_az = az
            self._last_el = el

        except Exception as e:
            logger.info(f"Something wrong appends in SunPosPublisher\n{e}")


