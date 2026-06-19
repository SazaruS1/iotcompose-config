import datetime
import json
import logging

import peewee

from core.models.device import Device
from core.models.record import Record

logger = logging.getLogger(__name__)



def process_welcome(topic,data):
    # Sans effet, sauf la demande de register si DEVICE inconnue
    ts = datetime.datetime.now()
    logger.debug(f"Receiving DATA: {topic}={data} @ {ts}")

    # L'UID dse trouve dans la payload (data)
    uid = data
    device = Device.get_or_none(uid=uid)

    if device is None:
        logger.warning(f"Device not found: uid={uid}")
        from .service import publish
        logger.warning(f"Asking for register")
        publish(f"{uid}/command", "REGISTER")


def process_data(topic, data):
    # On marque l'instant de réception du message
    ts = datetime.datetime.now()
    logger.debug(f"Receiving DATA: {topic}={data} @ {ts}")

    # On découpe le topic pour obtenir l'UID
    uid = topic.split('/')[0] # Ne peut pas déconner

    device = Device.get_or_none(uid=uid)
    if device is None:
        logger.warning(f"Device not found: uid={topic}")
        from .service import publish
        logger.warning(f"Asking for register")
        publish(f"{uid}/command", "REGISTER")
        return

    if not device.active:
        logger.info(f"Receiving data from inactive device {uid} -> ignoring")
        return

    # Extraction et validation de la valeur
    try:
        val = float(data)
    except ValueError:
        logger.info(f"Invalid MQTT data for {device} = {data}")
        return


    # On arrondi la valeur  (sauf si  delta_value = 0)
    # if device.delta_value != 0:
    #     rounded_val = device.delta_value * round(val / device.delta_value)
    # else:
    #     rounded_val = val

#    rounded_val = val
#    rounded_val = max(rounded_val, device.min_value)
#    rounded_val = min(rounded_val, device.max_value)

#    rounded_val = device.delta_value * round(rounded_val / device.delta_value)

    # On ne filtre pas les valeur.
#    if not device.min_value < rounded_val < device.max_value:
#        logger.warning(f"Receiving invalid data from {uid} -> ignoring : {rounded_val} (rounded value of {val}) not in [{device.min_value} , {device.max_value}]")
#        return

    # on peut mémoriser
    device.last_data_value = val
    device.last_data_at = ts
    device.save()

    Record.create(device=device, value=val, ts=ts, action=False)

     #BigBrother().notify(message.name)
#
def process_register(topic,data):
    # On marque l'instant de réception du message
    ts = datetime.datetime.now()
    logger.debug(f"Receiving REGISTER: {topic}={data} @ {ts}")

    print(f"Receiving REGISTER: {topic}={data}")
    print(f"**{data}")

    # Récupération du JSON
    try:
        dict = json.loads(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON for registering {e}")
        return

    # Validation des différents paramètres
    ok = True
    for key in ["uid", "description", "unit", "min_value", "max_value", "delta_value", "period",
                "min_period", "max_period", "read_only"]:
        ok = ok and (key in dict)

    if not ok:
        logger.warning(f"Malformed MQTT register")
        return

    # Pas de remplacement si le device existe déjà
    if Device.get_or_none(uid=dict["uid"]) is not None:
        logger.warning(f"Device {dict['uid']} already register")
        return

    # TODO: vérifier la structure des JSON...
    # Finalement... création
    try:
        device = Device.create(**dict)
    except peewee.PeeweeException as e:
        logger.warning(f"Unable to register device : {e}")
        return

    logger.info(f"Registering {device} done!")


#     print("----REGISTER ---------------------")
#     print(f"type={type}")
#     print(f"uid={uid}")
#     print(f"desc={description}")
#     print(f"unit={unit}")
#     print(f"min_value={min_value}")
#     print(f"max_value={max_value}")
#     print(f"delta_value={delta_value}")
#     print(f"period={period}")
#     print(f"min_period={min_period}")
#     print(f"max_period={max_period}")
#     print("----REGISTER ---------------------")
#
#     # On recherche le DEVICE s'il existe
#     device = Device.find_by_uid(uid)
#
#     if device is not None:
#         logger.warning(f"Register for already known device {uid}")
#         return
#
#     # On peut créer le Dévice
#     device = Device({
#         "uid": uid,
#         "description": description,
#         "unit": unit,
#
#         "min_value": min_value,
#         "max_value": max_value,
#         "delta_value": delta_value,
#
#         "period": period,
#         "min_period": min_period,
#         "max_period": max_period,
#         "read_only": True if "S" == type else False
#     })
#
#     device.save()
#
# def _decode_data(self, topic, payload):
#     #print(f"Processing datastore for {topic} {payload}")
#
#     # Le topic nous donne l'id du system
#
#     id = topic.split("/")[0]
#
#     # La payload est de la valeur transmise
#     try:
#         val = float(payload)
#         self._process_data(id, val)
#     except ValueError:
#         logger.info(f"Invalid MQTT datastore for {id} = {payload}")
#
# def _decode_register(self, payload):
#
#     # On décompose et on valide l'ensemble des champs
#     try:
#         info = json.loads(payload)
#     except json.decoder.JSONDecodeError as ex:
#         logger.info(f"Invalid MQTT register {payload}\n{ex}")
#         return
#
#     if type(info) is not dict:
#         logger.info(f"Invalid MQTT register {payload}")
#         return
#
#     # Validation des champs
#     ok = True
#     for key in ["type", "uid", "description", "unit", "min_value", "max_value", "delta_value", "period",
#                 "min_period", "max_period"]:
#         ok = ok and (key in info)
#
#     if not ok:
#         logger.info(f"Malformed MQTT register {payload}")
#         return
#
#     # On peut transmettre
#     self._process_register(**info)
#
#
# def publish(self,uid, value):
#     logger.info(f"MQTT Publishing {value} on topic {uid}/command")
#     self._mqtt_client.publish(f"{uid}/command", str(value))
#
# def ask_register(self, uid):
#     logger.info(f"Register needed for {uid}")
#     self._mqtt_client.publish(f"{uid}/core", "REGISTER")
#     def _on_message(client, userdata, message):
#
#         topic = message.topic
#         payload = str(message.payload.decode("utf-8"))
#         # print("=================================")
#         # print(f"{topic} = {payload}")
#         # print("=================================")
#
#         # Classement en fonction du topic
#         if re.match(r"^[a-zA-Z0-9_]+/datastore$", topic):
#             # Traitement d'une DATA
#             self._decode_data(topic, payload)
#             return
#         if re.match(r"^core/register$", topic):
#             # Traitement d'une DATA
#             self._decode_register(payload)
#             return
#
