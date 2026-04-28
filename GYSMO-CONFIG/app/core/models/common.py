import logging

import peewee
from dotenv import load_dotenv

import os

load_dotenv()


logging.getLogger(__name__).info(f"Using database: {os.getenv('DATABASE')}")

# TODO: Cette partie est spécifique à SQLITE...
database = peewee.SqliteDatabase(os.environ["DB_FILE"], pragmas={'foreign_keys': 1}) # Pour la vérification de FK et donc de la suppression en cascade...
#database.execute_sql('PRAGMA foreign_keys = ON;')


class BaseModel(peewee.Model):
    id = peewee.PrimaryKeyField()

    class Meta:
        database = database  # This model uses the "people.db" database.


