import logging

import numpy as np
import peewee as pw

from core.models.common import BaseModel

logger = logging.getLogger(__name__)


class Parameter(BaseModel):
    plugid = pw.CharField(unique=False)
    name = pw.CharField(null=False, max_length=50)
    value = pw.TextField(null=False)

    class Meta:
        # Le couple (pid,name) doit être unique
        indexes = (
            (('plugid', 'name'), True),
        )

    @staticmethod
    def set(plugid, name, value):
        param = Parameter.get_or_none(plugid=plugid, name=name)
        if param is None:
            Parameter.create(plugid=plugid, name=name, value=value)
        else:
            param.value = value
            param.save()

    @staticmethod
    def getDict(plugid):
        query = Parameter().select(Parameter.name, Parameter.value).where(Parameter.plugid == plugid)
        return {row['name']: row['value'] for row in query.dicts()}
