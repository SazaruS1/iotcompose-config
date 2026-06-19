import logging
from core.plugin import Plugin
logger = logging.getLogger(__name__)


class GymicPocMotorControl(Plugin):


    def webapps(self):
        from .webapp import webapp
        webapp.name = self.pid

        return [webapp]

    def tasks(self):
        from .task import GymicPocMotorControlTask
        task = GymicPocMotorControlTask(f"{self.pid}-task", self.pid)

        return [task]
