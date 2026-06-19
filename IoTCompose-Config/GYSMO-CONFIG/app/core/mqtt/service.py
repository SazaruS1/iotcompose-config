import datetime
import logging
import os
import re
import time

import dotenv
import paho.mqtt.client as mqtt

dotenv.load_dotenv()  # Chargement des variables d'environnement
logger = logging.getLogger(__name__)


client = None
connected = False

# #####################################################
# Déclaration des topics initiaux
# #####################################################
from .functions import process_data, process_welcome
from .functions import process_register

topics = {
    "+/data" : process_data,
    "system/register" : process_register,
    "system/welcome": process_welcome
}

_mapping = {}

def topic_to_regex(topic):
    # Remplace + par [^/]+
    topic = re.sub(r'\+', r'[^/]+', topic)
    # Remplace # par .*
    topic = re.sub(r'#', r'.*', topic)
    # Retourne le topic transformé
    return re.compile(topic)

def _build_mapping():
    global _mapping
    mapping  = {}
    for topic, func in topics.items():
        _mapping[topic_to_regex(topic)] = func

# #####################################################
# Récupération des données de configuration
# #####################################################
client_id = os.environ["MQTT_CLIENT_ID"]
user = os.environ["MQTT_USER"]
password = os.environ["MQTT_PASSWORD"]
host = os.environ["MQTT_BROKER"]
port = int(os.environ["MQTT_PORT"])

# #####################################################
# D&finition des différents callback
# #####################################################
def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    if reason_code == "Success":
        logger.info("Successfully connected to MQTT broker")
        connected = True
        _make_subscriptions(client)
        _build_mapping()
    else:
        connected = False
        logger.warning(f"Unable to connect to MQTT. Reason: {reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    global connected
    connected = False
    logger.warning(f"Disconected MQTT. Reason: {reason_code}")

#    """Callback pour la déconnexion."""
#    if reason_code != 0:
#        print("Déconnexion inattendue. Tentative de reconnexion...")
#        #reconnect(client)
#    else:
#        print("Déconnecté du broker MQTT")


def on_message(client, userdata, message):
    """Callback pour la réception de messages."""
    global _mapping
    topic = message.topic
    data = message.payload.decode()
    logger.debug(f"MQTT message : {topic} -> {data} ")
    for regex, func in _mapping.items():
        if bool(regex.match(topic)):
            func(topic,data)

def on_log(client, userdata, level, buf):
    pass

def on_subscribe(client, userdata, mid, reason_codes, properties):
    pass
    #logger.debug(f"Subscribing to topic: {mid}")

def on_unsubscribe(client, userdata, mid, reason_codes, properties):
    """Callback pour le désabonnement."""
    pass
    #logger.debug(f"Unsubscribing from topic: {mid}")

def on_publish(client, userdata, mid, reason_codes, properties):
    pass
    #print("Message publié")

# #####################################################
# Connexion, reconnection
# #####################################################

def _make_subscriptions(client):

    for topic in topics.keys():
        logger.info(f"Subscribing to topic {topic}")
        client.subscribe(topic)  # Toutes les valeurs

# #####################################################
# Connexion, reconnection
# #####################################################

# def connect(client):
#     """Connecter le client au broker MQTT."""
#     global connected
#     try:
#         client.connect(host=host, port=port, keepalive=15)
#         client.loop_start()  # Démarrer la boucle de gestion des événements MQTT
#     except Exception as e:
#         connected = False
#         logger.warning(f"MQTT - Connection error: {e}")
#         time.sleep(5)
#         connect(client)

# #####################################################
# Création du client MQTT
# #####################################################

def start():
    logger.info("Starting MQTT service")
    global client, connected
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=client_id)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_log = on_log
    client.on_subscribe = on_subscribe
    client.on_unsubscribe = on_unsubscribe
    client.on_publish = on_publish

    client.reconnect_delay_set() # force la reconnexino en cas de déconnexction

    # Intègre la gestion des reconnections -> inutile (et faux) de le faire à la main.
    client.loop_start()  # Démarrer la boucle de gestion des événements MQTT

    try:
        client.connect(host=host, port=port, keepalive=15)
    except Exception as e:
        connected = False
        logger.error(f"MQTT - Connection error: {e}")


def stop():
    global client
    client.loop_stop()
    client.disconnect()


def publish(topic, data):
    global client
    client.publish(topic,data)

