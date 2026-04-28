import logging

from core.models import Parameter
from core.plugin import Plugin
from core.utils import safe_int

logger = logging.getLogger(__name__)


class RuleEnginePlugin(Plugin):
    def webapps(self):
        # On enregistre la partie web
        from .webapp import webapp
        webapp.name = self.pid

        return [webapp]

    def tasks(self):
        # # On récupère le paramètre de durée de la période
        # param = Parameter.get_or_none(uid=self.pid, name="period")
        # if param is None:
        #     Parameter.create(uid=self.pid, name="period", value=60)
        #     period = 60
        # else:
        #     period = safe_int(param.value)

        from plugins.rule_engine.task import RuleEngineTask
        task = RuleEngineTask(f"{self.pid}-task", self.pid)
        #task.set_period(period)

        return [task]
