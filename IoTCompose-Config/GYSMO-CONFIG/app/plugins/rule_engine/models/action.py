from core.models.common import BaseModel
import peewee as pw

from plugins.rule_engine.models.rule import Rule


class Action(BaseModel):
    variable = pw.CharField(max_length=50, null=False)
    value = pw.CharField(max_length=50, null=False)

    rule = pw.ForeignKeyField(Rule, backref='actions',on_delete='CASCADE')

    def __str__(self):
        return f"Action {self.variable} = {self.value}"
