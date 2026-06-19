from core.plugin import Plugin

import logging
logger = logging.getLogger(__name__)


class UserVariablePlugin(Plugin):

    def webapps(self):
        from .webapp import webapp
        webapp.name = self.pid # Obligatoire

        return [webapp]



