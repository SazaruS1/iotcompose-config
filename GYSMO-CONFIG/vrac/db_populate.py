import datetime

from core.models import database, creates_tables_if_necessary
from core.models.device import Device
from core.models.user import User

creates_tables_if_necessary()

user_data = [
    {'username': 'admin', 'email': 'admin@gysmo.com', 'password': "admin"},
    {'username': 'user', 'email': 'user@gysmo.com', 'password': "user"},
]
device_data = [
    {'uid': "007",
     'description': "Un capteur de test",
     'name': "Température_eau",
     'unit': "°C",

     'min_value': -5,
     'max_value': 55,
     'delta_value': 0.2,

     'period': 60,
     'min_period': 0,
     'max_period': 3600,

     'created_at': datetime.datetime.now(),
     'validated_at': None,
     'validated_by': None,

     'read_only': True,
     'virtual': False,
     'active': True,
     'last_data_value': None,
     'last_data_at': None
     }

]

# Users
print(f'Deleting {User.delete().execute()} user(s)')
with database.atomic():
    for data in user_data:
        user = User.create(**data)
        print(f"Inserting {user}")

# Users
print(f'Deleting {Device.delete().execute()} device(s)')
with database.atomic():
    for data in device_data:
        device = Device.create(**data)
        print(f"Inserting {device}")
