import logging

import numpy as np
import peewee as pw

from core.models.common import BaseModel
from .device import Device

logger = logging.getLogger(__name__)

class Record(BaseModel):
    ts = pw.DateTimeField(null=False)
    value = pw.DoubleField(null=False)
    action = pw.BooleanField(null=False, default=False)
    device = pw.ForeignKeyField(Device, backref='records', on_delete='CASCADE')
