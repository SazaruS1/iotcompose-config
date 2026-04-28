import logging

from core.models import Parameter
from core.task import Task
from core.utils import safe_int

logger = logging.getLogger(__name__)


class RuleEngineTask(Task):

    def execute(self, time, did, force):
        # Effectue une itération du moteur de règle:
        logger.info(f"Itération of Rule Engine {self.plugid} @ {time}")

        from .engine import process
        process(self.id, time)

    def sync(self,params):

        # Par convention, les paramètres sont réatachés au PLUGIN mais non à la tache
#        param = Parameter.get_or_none(plugid=self.plugid, name="period")
#        if param is None:
#            Parameter.create(plugid=self.plugid, name="period", value=60)
#            period = 60
#        else:
#            period = safe_int(param.value,1)#

        self.set_period(safe_int(params.get("period"),10))
