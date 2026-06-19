import logging

from core.plugin import Plugin

logger = logging.getLogger(__name__)


class SunPosPublisherPlugin(Plugin):

    def webapps(self):
        from .webapp import webapp
        webapp.name = self.pid # Obligatoire

        return [webapp]

    def tasks(self):
        from .task import SolarPositionTask
        task = SolarPositionTask(f"{self.pid}-task", self.pid)

        return [task]


