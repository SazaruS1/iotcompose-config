import logging

from core.models import database

from .rule import Rule
from .premise import Premise
from .action import Action

logging.getLogger(__name__).info("[Rule Engine] Creating tables...")
database.create_tables([Action, Premise, Rule])


