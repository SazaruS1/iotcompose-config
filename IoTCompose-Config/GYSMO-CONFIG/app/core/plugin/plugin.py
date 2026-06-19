import logging

logger = logging.getLogger(__name__)


class PluginException(Exception):
    pass


class Plugin:
    """Classe (abstraite) en charge de gérer la description et l'état d'un Plugin."""

    def __init__(self, pid, prefix, menu_name=None):
        self._pid = pid
        self._prefix = prefix
        self._menu_name = menu_name

    @property
    def pid(self):
        return self._pid

    @property
    def prefix(self):
        return self._prefix

    @property
    def menu_name(self):
        return self._menu_name

    #def start(self):
    #    pass

    #
    #def stop(self):
    #    pass

    # Ces deux méthodes doivent retourner les apps et les tasks qui seront enregistrées
    # Attention, elles ne doivent être utilisées QUE lors du lancement de l'applucation
    # Pour retrouver les Tasks et le Webapps en runtime, il faut interroger le PluginManager.
    def webapps(self):
        logger.warning(f"Calling webapps() on abstract class Plugin")
        return []

    def tasks(self):
        logger.warning(f"Calling tasks() on abstract class Plugin")
        return []
