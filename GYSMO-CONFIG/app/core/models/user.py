import datetime
import logging
from peewee import *

from core.models.common import BaseModel

logger = logging.getLogger(__name__)


class User(BaseModel):
    username = CharField(unique=True)
    password = CharField(null=True)
    email = CharField(unique=True)

    created_at = DateTimeField(default = datetime.datetime.now())
    last_connection_at = DateTimeField(default=datetime.datetime.now())

    def __str__(self):
        return f"User[{self.id}] {self.username} ({self.email})"