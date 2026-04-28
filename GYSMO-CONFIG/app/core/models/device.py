import datetime
import logging

import numpy as np
import peewee as pw

from core.models.common import BaseModel

logger = logging.getLogger(__name__)


class Device(BaseModel):
    uid = pw.CharField(unique=True)
    description = pw.TextField(null=True)
    name = pw.CharField(null=True, max_length=50, unique=True)
    unit = pw.CharField(null = True, max_length=50)

    min_value = pw.DoubleField(default=-np.inf)
    max_value = pw.DoubleField(default=+np.inf)
    digits = pw.IntegerField(default=15)

    period = pw.DoubleField(default=3600)
    min_period = pw.DoubleField(default=0)
    max_period = pw.DoubleField(default=+np.inf)

    created_at = pw.DateTimeField(default=datetime.datetime.now())
    validated_at = pw.DateTimeField(null=True)
    validated_by = pw.CharField(null=True, max_length=50)

    read_only = pw.BooleanField(default=True)
    virtual = pw.BooleanField(default=False)
    active = pw.BooleanField(default=False)

    # La dernière donnée reçue du capteur. Pertinent quelle que soit la valeur de read_only
    last_data_value = pw.DoubleField(null=True)
    last_data_at = pw.DateTimeField(null = True)

    # La dernière donnée (action) transmise vers l'actionneur. N'est pertinent que pour read_only=False
    last_action_value = pw.DoubleField(null=True)
    last_action_at = pw.DateTimeField(null = True)


    def __str__(self):
        return f"Device[{self.id}] {self.name} ({self.uid})"