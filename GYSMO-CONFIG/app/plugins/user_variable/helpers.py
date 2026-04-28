import numpy as np
from core.models import Device
from peewee import fn

def create_user_var(uid, name, description, unit, min_value=-np.inf, max_value=np.inf, digits=0):
    json = {
        "uid": uid,
        "description": description,
        "unit": unit,
        "name": name,

        "min_value": min_value,
        "max_value": max_value,
        "digits": digits,

        "period": 0,
        "min_period": 0,
        "max_period": 0,

        "validated_by": "internal",
        "active": True,

        "read_only": False, # -> Permet la distinction entre tache auto et variables utilisateur
        "virtual": True
    }

    # on regarde s'il existe
    dev = Device.get_or_none(
        (Device.uid == uid) | (fn.LOWER(Device.name) == name.lower())
    )
    if dev is None:
        # Création
        dev = Device.create(**json)
    else:
        # Mise à jour
        dev = None

    return dev


def update_user_var(uid, name, description, unit, min_value, max_value):
    json = {
        "uid": uid,
        "description": description,
        "unit": unit,
        "name": name,

        "min_value": min_value,
        "max_value": max_value,
        "digits": digits,

        "period": 0,
        "min_period": 0,
        "max_period": 0,

        "validated_by": "internal",
        "active": True,

        "read_only": True,
        "virtual": True
    }

    # on regarde s'il existe
    dev = Device.get_or_none(
        (Device.uid == uid) | (fn.LOWER(Device.name) == name.lower())
    )
    if dev is None:
        # Création
        dev = Device.create(**json)
    else:
        # Mise à jour
        dev = None

    return dev