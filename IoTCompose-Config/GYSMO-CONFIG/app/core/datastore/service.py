import datetime

from core.models import Device, Record
from plugins.solar_position import logger


# def get_last(name):
#     """ retourne un tuple contenant le nom, la dernière valeur et le timestamp
#     """
#
#     result = Device.select().where((Device.active) and (Device.name==name)).get_or_none()
#
#     if result is None:
#         return None, None, None
#
#     return result.name, result.last_data_value, result.last_data_at


def pull(name = None):
    """ retourne une liste dictionnaire (nom, dernière valeur valide) pour les seuls devices actifs
    """
    query = Device.select(Device.name, Device.last_data_value).where(Device.active)
    if name is not None:
        # On recherche spécifiquement un nom de device
        query = query.where(Device.name == name)

    result_dict = {device['name']: device['last_data_value'] for device in query.dicts()}
    return result_dict

def push(data):
    """
    Pousse les nouvelles valeurs dans la base (si existe).
    """

    import core.mqtt as mqtt_service

    #print(f"devra mettre à jour les données\n{data}")
    # Si c'est un "READ_ONLY" ie un SENSOR, on pousse la valeur directement via MQTT
    # Sinon on enregistre en base et on pousse le message MQTT
    # TODO: A Changer

    ts = datetime.datetime.now()
    for (name, value) in data.items():
        #print(f"{name} => {value}")
        device = Device.get_or_none(name=name)
        if device is None:
            logger.warning(f"Traying to save value for undefined device with name {name}")
        else:
            if device.read_only:
                # C'est un capteur -> on pousse le message MQTT
                # La mise à jour de last_data_* est automatique via la réception de ce message
                mqtt_service.publish(f"{device.uid}/data", value)
            else:
                # C'est un actionneur, on enregistre en base et on publie
                #_upsert_record(device=device, value=value, ts=ts, action=True)
                #Record.create(device=device, value=value, ts=ts, action=True)
                try:
                    Record.create(device=device, value=value, ts=ts, action=True)
                except Exception as e:
                    print(f"Erreur lors de la création de l'enregistrement : {e}")
                # On met à jour la valeur
                device.last_action_value = value
                device.last_action_at = ts
                device.save()

                mqtt_service.publish(f"{device.uid}/action",value)




def _upsert_record(device, value, ts,action=False):
    # Récupérer l'utilisateur existant
    # TODO: très bizarre ici ??? Pourquoi un UPSERT ?????
    record = Record.get_or_none(device == device)
    if record is None:
        Record.create(device=device, value=value, ts=ts,action=action)
    else:
        # Mise à jour
        record.value = value
        record.ts = ts
        record.action = action
        record.save()  # Sauvegarder les modifications
