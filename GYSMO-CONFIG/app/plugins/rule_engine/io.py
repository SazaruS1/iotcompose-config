#     # ======================================================================================================
#     # IMPORT / EXPORT des règles
#     # ======================================================================================================
#
import json
import logging
import re

from plugins.rule_engine.engine import RuleEngineException
from plugins.rule_engine.models import Rule, Premise, Action


logger = logging.getLogger(__name__)

def _decode_duration(string: str):
    string = string.strip().upper()
    val = int(string[0:-1])
    if string[-1] == "S":
        pass
    elif string[-1] == "M":
        val = val * 60
    elif string[-1] == "H":
        val = val * 60 * 60
    else:
        raise RuleEngineException(f"Invalid duration: {string}")
    return val


def _decode_if(string: str):
    string = string.strip()#.upper()
    # On découpe selon les espaces
    parts = re.split(r"\s+", string)
    operateurs = ['<>', '==', '<', '>', "<=", ">="]

    if len(parts) < 3:
        raise Exception(f"Erreur de syntaxe: {string}")

    if parts[1] not in operateurs:
        raise Exception(f"Erreur de syntaxe: l'opérateur {parts[1]} est inconnu dans {string}")

    if len(parts) == 4:  # On regarde la période de maintien
        pattern = re.compile(r'\[([^\]]*)\]')
        match = pattern.search(parts[3])
        if not match:
            raise RuleEngineException(f"Syntax error: {string}")
        hold_delay = _decode_duration(match.group(1))
    else:
        hold_delay = 0

    return {"operand1": parts[0], "operand2": parts[2], "operator": parts[1], "hold_delay": hold_delay}


def _decode_then(string: str):
    string = string.strip()#.upper()
    # On découpe selon les espaces
    parts = string.split("=", maxsplit=1)

    if len(parts) != 2:
        raise RuleEngineException(f"Syntax error: {string}")

    return {"variable": parts[0].strip(), "value": parts[1].strip()}


#


def parse(code, uid):

    # ----------------------------------------
    # Etape 0 : Nettoyage
    # ----------------------------------------
    lines = code.split("\n")
    lines = [l.rstrip('\n').split('!', 1)[0].strip() for l in lines]

    # ----------------------------------------
    # Etape 1 : Décomposition en règles
    # ----------------------------------------

    # Regroupement par règle (ie context)
    # Contexts est un disctionnaire dont les clés sont les nom des règles et les valeurs sont des listes qui
    # contiennent toutes les lignes qui appartiennent à cette règle
    current = None
    contexts = {}
    for l in lines:
        if len(l) == 0:
            continue  # On saute les lignes vides

        if l.startswith("RULE"):
            parts = re.split(r'\s+', l)  # On découpe au premier bloc d'espaces
            if len(parts) != 2:
                raise RuleEngineException(f"Syntax error: {l}")
            if parts[1] in contexts:
                raise RuleEngineException(f"Rule with name {parts[1]} already exists")
            current = contexts[parts[1]] = []
            continue

        # on ajoute au contexte
        if current is None:
            raise RuleEngineException(f"Syntax error: {l}")

        current.append(l)

    # ----------------------------------------
    # Etape 3 : Analyse individuelle des règles
    # ----------------------------------------
    rules = []

    for name, list in contexts.items():
        # Pour chaque règle (dont le nom est name), on analyse la liste des lignes qui lui appartiennent
        description = []
        premises = []
        actions = []
        priority = 0
        sleep = 0

        for l in list:
            if l.startswith("\""):  # Commentaire
                description.append(l[1:])

            if l.startswith("PRIORITY"):
                priority = int(l[len("PRIORITY"):])

            if l.startswith("SLEEP"):
                sleep = _decode_duration(l[5:])

            if l.startswith("IF"):
                tmp = _decode_if(l[len("IF"):])
                premises.append(tmp)

            if l.startswith("THEN"):
                tmp = _decode_then(l[len("THEN"):])
                actions.append(tmp)

        # On construit le dictionnaire qui va bien
        rules.append( {"name": name, "plugin": uid,
                "description": "\n".join(description), 'priority': priority,
                'disable_delay': sleep,
                "premises" : premises,
                "actions" : actions})

    # ----------------------------------------
    # Etape 4 : Insertion en base (finalement)
    # ----------------------------------------

    try:
        with Rule._meta.database.atomic():
            # Suppression des informations existantes (pour cet uid)

            subquery = Rule.select(Rule.id).where(Rule.plugin == uid)
            Premise.delete().where(Premise.rule.in_(subquery)).execute()
            Action.delete().where(Action.rule.in_(subquery)).execute()
            Rule.delete().where(Rule.plugin == uid).execute()

            for rule in rules:
                r = Rule.create(name=rule["name"],
                                plugin=rule["plugin"],
                                description=rule["description"],
                                priority=rule["priority"],
                                disable_delay=rule["disable_delay"])
                for p in rule["premises"]:
                    prem = Premise.create(**p, rule=r)
                for a in rule["actions"]:
                    act = Action.create(**a, rule=r)

    except Exception as e:
        logger.warning(f"Rule Engine (Import) - An error occurred: {e}")

    logger.info(f"{len(rules)} rules imported")

def dump(uid):
    # routine pour exporter les règles
    query =  Rule.select().where(Rule.plugin == uid)

    print("-" * 80)
    for r in query:
        print(f"{r.name} : {r.description}")
        print(f" | priority = {r.priority}")
        print(f" | disable_delay = {r.disable_delay} s")
        print(f" | trigger_count = {r.trigger_count}")
        print(f" | triggered_at = {r.triggered_at}")
        print(f" |-- IF")
        for p in r.premises:
            print(f"    {p.operand1} {p.operator} {p.operand2} DURING {p.hold_delay} s")
        print(f" |-- THEN")
        for a in r.actions:
            print(f"    {a.variable} {a.value}")

        print("-" * 80)

def export_as_dict(uid):
    """ Exporte les règles sous forme de JSON """
    res = []

    query = Rule.select().where(Rule.plugin == uid)
    for r in query:
        item =  {
            "name": r.name,
            "description": r.description,
            'priority': r.priority,
            'disable_delay': r.disable_delay,
            "premises" : [],
            "actions" : []
        }
        for p in r.premises:
            item["premises"].append({
                "operand1": p.operand1,
                "operand2": p.operand2,
                "operator": p.operator,
                "hold_delay": p.hold_delay
            })
        for a in r.actions:
            item["actions"].append({
                "variable": a.variable,
                "value": a.value
            })
        res.append(item)

    return res