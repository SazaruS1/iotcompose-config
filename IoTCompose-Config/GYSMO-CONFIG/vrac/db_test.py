import logging

import peewee

from core.models import database, BaseModel, creates_tables_if_necessary
from core.models.user import User
from core.models.device import Device
from core.models.message import Message
from core.models.parameter import Parameter
from core.models.record import Record

logging.basicConfig(  # filename='logs/caubios.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

logger.info("Beginning tests")

creates_tables_if_necessary()


#User.create(username="bob", email="bob@mail.com")

user = User.get_or_none(username="bob")
print(user)
user = User.get_or_none(1)
print(user)



