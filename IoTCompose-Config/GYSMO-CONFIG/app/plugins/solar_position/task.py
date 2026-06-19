from datetime import timedelta, timezone
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

        self._last_utc = None
        self._last_tsv = None
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

        json_tsv = {
            "uid": "tsv_uid",
            "description": "Temps Solaire Vrai",
            "unit": "h",
            "name": "tsv",

            "min_value": 0,
            "max_value": 24,
            "digits": 5,

            "period": 0,
            "min_period": 0,
            "max_period": 0,

            "validated_by": "internal",
            "active": True,

            "read_only": True,
            "virtual": True
            }
        
        json_local_time = {
            "uid": "local_time_uid",
            "description": "Heure légale",
            "unit": "h",
            "name": "time",

            "min_value": 0,
            "max_value": 24,
            "digits": 5,

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

        dev_tsv = Device.get_or_none(uid="tsv_uid")
        if dev_tsv is None:
            # on cherche si par hazard on a conservé le même nm
            dev_tsv = Device.get_or_none(name="tsv")
        if dev_tsv is None:
            # Création
            Device.create(**json_tsv)
        else:
            # Mise à jour
            Device.update(**json_tsv).where(Device.id == dev_tsv.id).execute()

        dev_time = Device.get_or_none(uid="local_time_uid")
        if dev_time is None:
            # on cherche si par hazard on a conservé le même nm
            dev_time = Device.get_or_none(name="time")
        if dev_time is None:
            # Création
            Device.create(**json_local_time)
        else:
            # Mise à jour
            Device.update(**json_local_time).where(Device.id == dev_time.id).execute()


    def execute(self, utc, did, force):

        # On exécute la tâche
        logger.info(f"Itération of {self.plugid} @ {utc}")
        try:
            
            # Position
            pos = suncalc.get_position(utc, self._longitude,self._latitude)

            az = float(np.degrees(pos["azimuth"]))
            el = float(np.degrees(pos["altitude"]))

            # temps solaire vrai
            times = suncalc.get_times(utc, self._longitude, self._latitude)
            solar_noon = times['solar_noon']  # ex: 2024-06-16 11:23:00+00:00
            
            true_solar_time = ((utc - solar_noon.replace(tzinfo=timezone.utc)).total_seconds() / 3600 + 12) % 24
            
            local_time = utc.astimezone()


            data = {
                self._az_name: az,
                self._el_name: el,
                "tsv": true_solar_time,
                "time": local_time.hour + local_time.minute / 60 + local_time.second / 3600
            }

            ds.push(data)

            self._last_utc = utc.hour + utc.minute / 60 + utc.second / 3600 # L'heure UTC
            self._last_tsv = true_solar_time
            self._last_az = az
            self._last_el = el

        except Exception as e:
            logger.info(f"Something wrong appends in SunPosPublisher\n{e}")


