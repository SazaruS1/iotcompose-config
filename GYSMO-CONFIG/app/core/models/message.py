import datetime
import logging

import numpy as np
import peewee as pw

from core.models.common import BaseModel

logger = logging.getLogger(__name__)



class Message(BaseModel):
    STATUS = (
        (0, 'Info'),
        (1, 'Warning'),
        (2, 'Error')
    )

    level = pw.SmallIntegerField(choices=STATUS, default=0)
    message = pw.TextField(null=False)
    must_validate = pw.BooleanField(default=True)

    created_at = pw.DateTimeField(default=datetime.datetime.now())
    validated_at = pw.DateTimeField(null=True)
    validated_by = pw.CharField(null=True, max_length=50)

    @staticmethod
    def log(message):
        Message.create(level=0, message=message, must_validate=False)

