from datetime import timezone
import logging
import re
from core import datastore

import core.mail as mail_service

from core.models import Record, Message
from core.task import Task
from plugins.rule_engine.models import Premise, Action, Rule

logger = logging.getLogger(__name__)


class RuleEngineException(Exception):
    pass

def _substitute(string, old, new):
    # ex: "La valeur de la température est passé de {temp.pre} à {temp}
    for k in old.keys():
        string = string.replace("[{cle}.pre]".format(cle=k), str(old[k]))
    for k in new.keys():
        string = string.replace("[{cle}]".format(cle=k), str(new[k]))
    for k in old.keys():
        string = string.replace("[{cle}]".format(cle=k), f"{old[k]}")
    return string


def _execute(messages : list[tuple[str,str]],data_old,data_new):


    for k, v in messages:
        k = k.upper()
        v = _substitute(v, data_old, data_new)
        if k == "@EMAIL":
            mail_service.send(v)
        elif k == "@INFO":
            Message.create(message=v, level=0, must_validate=False)
        elif k == "@WARNING":
            Message.create(message=v, level=1, must_validate=False)
        elif k == "@ERROR":
            Message.create(message=v, level=2, must_validate=False)
        elif k == "@INFO.ACK":
            Message.create(message=v, level=0, must_validate=True)
        elif k == "@WARNING.ACK":
            Message.create(message=v, level=1, must_validate=True)
        elif k == "@ERROR.ACK":
            Message.create(message=v, level=3, must_validate=True)
        else:
            logger.debug(f"Rule Engine doesn't know what to do with {k}={v}")

def _update_rules(uid,now):

    # ON parcours toutes les règles de la
    query =  Rule.select().where(Rule.plugin == uid)

    for r in query:

        if r.triggered_at is not None and (now - r.triggered_at.replace(tzinfo=timezone.utc)).seconds < r.disable_delay:
            # La règle est dans sa periode "refractaire" -> on ne traite pas
            r.triggerable = False
            r.save()  # TODO: mettre un mécanisme pour éviter les sync inutiles vers la base
            continue

        # On regarde si les prémisses sont toutes OK
        ok = True
        for p in r.premises:
            ok = ok and p.state

        r.triggerable = ok
        r.save()

def _extract( op, ds):
    # op peut être:
    # - un nombre -> on le retourne
    # - une chaine qui représente un nombre valide -> on le retourne
    # - une chaine qui correspond à une donnée -> on retourne la valeur associée
    # - rien -> c'est une erreur -> on retourne None

    if isinstance(op, (float, int)):
        return float(op)

    if not isinstance(op, str):
        return None

    if op.isnumeric():
        return float(op)

    return ds.get(op, None)


def _evaluate(ds, op1, op2, oper):
    val1 = _extract(op1, ds)
    val2 = _extract(op2, ds)

    if val1 is None:
        logger.warning(f"Value {op1} is undefined")
        return
    if val2 is None:
        logger.warning(f"Value {op2} is undefined")
        return

    # On effectue la comparaison

    match oper:
        case "<":
            return val1 < val2
        case ">":
            return val1 > val2
        case "<=":
            return val1 <= val2
        case ">=":
            return val1 >= val2
        case "<>":
            return val1 != val2
        case "==":
            return val1 == val2
        case _:
            logger.warning(f"unknown operator {oper}")
            return False


def _update_premises(uid,now_utc, data):

    subquery = Rule.select(Rule.id).where(Rule.plugin == uid)
    query = Premise.select().where(Premise.rule.in_(subquery))

    for p in query:
        condition = _evaluate(data, p.operand1, p.operand2, p.operator)
        if condition is None:
            raise RuleEngineException(
                f"Unable to evaluate condition of premise {p} for rule {p.rule} of {uid}"
            )
        # Si la condition est Vraie, on enregistre l'instant de basculement
        if condition:
            if p.true_ts is None:
                p.true_ts = now_utc
            # On fixe l'état de la prémisse (avec tempo)
            p.state = (now_utc - p.true_ts.replace(tzinfo=timezone.utc)).seconds >= p.hold_delay

        else:  # On reset l'instant de basculement
            #p.test = False
            p.true_ts = None
            p.state = False

        p.save()

def _trigger(uid, now_utc,data):

    # On applique toutes les règles déclenchables par ordre de priorité croissante
    data_changes = dict()
    messages : list[tuple[str,str]] = [] # On transforme en liste de tuple (type, message)

    query = Rule.select().where((Rule.plugin == uid) & Rule.triggerable).order_by(Rule.priority.desc())


    for r in query:  # pour chaque règle déclencheable
        for a in r.actions:
            if a.variable.startswith("@"):
                messages.append((a.variable, a.value))
            else:
                # on recherche la valeur de "Value"
                val = _extract(a.value, data)
                if val is None:
                    pass
                    # TODO : lever une exception...
                else:
                    data_changes[a.variable] = a.value

    return data_changes, messages


def process(uid, now_utc):

    # Effectue une itération du moteur de règle:
    logger.info(f"Itération of Rule Engine {uid} @ {now_utc}")

    # On récupère les données (dictionnaire)
    data = datastore.pull()

    # 1) mise à jour des PREMISSES
    _update_premises(uid, now_utc,data)

    # 2) mise à jour de l'état de la déclenchabilité des règles...
    _update_rules(uid,now_utc)

    # 3) déclenchement des règles
    data_changes, messages = _trigger(uid, now_utc, data )

    # On traite les modifications
    datastore.push(data_changes)

    # On enregistre/effectue les actions
    _execute(messages, data,data_changes)
