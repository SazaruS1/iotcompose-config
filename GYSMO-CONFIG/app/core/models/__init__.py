import logging

from .device import Device
from .message import Message
from .parameter import Parameter
from .record import Record
from .user import User


# def creates_tables_if_necessary():
#     from core.models.user import User
#     from core.models.device import Device
#     from core.models.message import Message
#     from core.models.parameter import Parameter
#     from core.models.record import Record


from core.models.common import database

logging.getLogger(__name__).info("Creating tables...")

database.create_tables([User, Device, Message, Parameter, Record])
