import logging

from core.models import Parameter
from core.plugin import PluginException

logger = logging.getLogger(__name__)

logger.info("Initializing Plugin Service")

# La liste des plugins connus
_plugins = {}

def sync(plugid):
    """
    Lance la synchronisation de toutes les TASKS qui appartiennent au plugin <<plugin>>
    """
    global _plugins

    plugin = _plugins.get(plugid)
    if plugin is None:
        logger.warning(f"Trying to synchronise non exsiting {plugid}")
        return

    # On récupère le dictinnaire des paramètres qui existent pour ce plugin
    # On synchronise

    params = Parameter.getAll(plugid)
    for t in plugin.tasks:
        t.sync(params)

def add(plugin: "Plugin"):
    global _plugins

        # if self._running:
        #     raise PluginException("PluginService: trying to register plugin after start")

    # Contrôles préliminiares
    if not hasattr(plugin, "pid"):
        logger.error("PluginService: trying to register non Plugin object")
        raise PluginException("PluginService: trying to register non Plugin object")

    if plugin.pid in _plugins:
        logger.error(f"Plugin with uid={plugin.plugid} is already known")
        raise PluginException(f"Plugin with uid={plugin.plugid} is already known")

    # On est bon
    _plugins[plugin.pid] = plugin

def start(prod=False):
    global _plugins

    import core.web as web_service
    import core.task as task_service

    # Pour chaque plugin
    for p in _plugins.values():
        for w in p.webapps():
            web_service.load(w,p)

        for t in p.tasks():
            task_service.register(t)
            t.sync(Parameter.getDict(p.pid))

    web_service.start(prod)
    task_service.start()

    logger.info("Plugin Service started")
    #self._running = True

def stop():
    global _plugins
#    # Arrête tous les plugins
    # PAS UTILE A CAR fait dans taskservice.stop()
#    for p in _plugins.values():
#        p.stop()
    #self._running = False # Inutile car l'arret des plugins ne se fait qu'à la terminaison de l'appli

    import core.web as webservice
    import core.task as taskservice

    webservice.stop()
    taskservice.stop()

def dump():
    global _plugins
    for p in _plugins.values():
        print(f"> {p.pid} @ {p.prefix}")


