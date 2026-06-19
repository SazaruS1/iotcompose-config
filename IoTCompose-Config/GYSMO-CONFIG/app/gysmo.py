

import logging
import os
import signal
from time import sleep

from dotenv import load_dotenv

from core.models import Message

# ======================================================
# Chargement des variables d'environnement
# ======================================================

load_dotenv()

# ======================================================
# Déclaration et configuration du logger (code)
# ======================================================
logging.basicConfig(  # filename='logs/caubios.log',
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

logger = logging.getLogger(__name__)
logger.info("Starting up GYSMO...")

# # ======================================================
# # Initialisation des services
# # ======================================================
# import core.mqtt as mqtt_service
# #import core.system as task_service
# #import core.web as web_service
# #import core.mail as mail_service
# import core.plugin as plugin_service
#
#
# ======================================================
# Chargement des plugins
# ======================================================

import core.system as bigboss

#wp = WelcomePlugin("welcome", "/", "Accueil")
#bigboss.add_plugin(wp)
#plugin_service.add(wp)
#wp = WelcomePlugin("welcome2", "/2", "Accueil2")
#bigboss.add_plugin(wp)
#plugin_service.add(wp)


bigboss.load_plugins("plugins.yaml")

# ======================================================
# Démarrage des services
# ======================================================
#mqtt_service.start()
#web_service.start(prod=False)

#plugin_service.start()
#task_service.start()


bigboss.start()
Message.log("Starting GYSMO")

import core.mail as mail_service
mail_service.send("Server just (re)started")

#plugin_service.dump()
#web_service.dump()
#task_service.dump()

running  = True
def interrupt_handler(_signo, _stack_frame):
    logger.info(f"** Shuting down... {_signo}")
    global running
    running = False

signal.signal(signal.SIGTERM, interrupt_handler)
signal.signal(signal.SIGINT, interrupt_handler)
signal.signal(signal.SIGHUP, interrupt_handler)

print(os.getpid())
# Pour avoir les infos de débug de peewee
#logger = logging.getLogger('peewee')
#logger.addHandler(logging.StreamHandler())
#logger.setLevel(logging.DEBUG)

# ======================================================
# Boucle infinie d'attente...
# ======================================================
#Message.add("Starting", Message.INFO, False)

#web.send_email("Starting")

while running:
    sleep(1)

logger.info("Stopping...")

bigboss.stop()
#plugin_service.stop()
#mqtt_service.stop()

logger.info("Stopping... Bye")


