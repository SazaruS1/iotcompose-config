from core.models.common import BaseModel
import peewee as pw

from plugins.rule_engine.models.rule import Rule


class Premise(BaseModel):
    operand1 = pw.CharField(max_length=50, null=False)
    operator = pw.CharField(max_length=50, null=False)
    operand2 = pw.CharField(max_length=50, null=False)

    rule = pw.ForeignKeyField(Rule, backref='premises', on_delete='CASCADE')

    # Le temps pendant lequel la condition doit être VRAIE pour que la premisse soit considérée comme VRAIE
    hold_delay = pw.IntegerField(default=0, null=False)

#    # La dernière évaluation de la condition
#   # TODO: n'est pas forcément utile,
#    test =  pw.BooleanField(default=False, null=False)

    # L'instant où la condition a été évaluée comme VRAIE
    true_ts = pw.TimestampField(null=True, default=None)

    # La valeur de la prémisse (condition+delai)
    state = pw.BooleanField(default=False, null=False)

    def __str__(self):
        if self.true_ts is None:
            return f"Premise {self.operand1}{self.operator}{self.operand2}"
        else:
            return f"Premise {self.operand1}{self.operator}{self.operand2} [True since {self.true_ts}]"
