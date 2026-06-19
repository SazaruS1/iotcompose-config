import glob
import importlib
import logging
import os
import sys
import threading
import time
import datetime
import uuid

from core.models import Parameter
from core.task.declaration import Task, TaskException

logger = logging.getLogger(__name__)

# =======================================================
# Déclaration des variables globales
# =======================================================

_tasks = {}  # dictionnaire des tâches à gérer
_running = False  # On ne peut plus ajouter après démarrage

_thread = None
_lock = threading.Lock()

_changed_vars = set()
_changed_lock = threading.Lock()


def notify_change(did: str):
    with _changed_lock:
        _changed_vars.add(did)

# =======================================================
# Routine (thread) principal d'exécution des tasks
# =======================================================
def _run_thread():
    logger.info("TaskThread started")
    global _changed_vars
    while _running:
        now = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"TaskThread loop @ {now}")
        tasks_to_fire: list[tuple[Task, str | None]] = []

        # Récupère et vide les changements accumulés
        with _changed_lock:
            dids = _changed_vars
            _changed_vars = set()

        # On identifie les Task a lancer
        with _lock:
            for task in _tasks.values():
                if dids:
                    for did in dids:
                        if task.fire(did):
                            tasks_to_fire.append((task, did))
                elif task.fire():
                    tasks_to_fire.append((task, None))

        # On les exécute
        for task, did in tasks_to_fire:
            try:    
                task.launch(now,did, force=False)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Task {task} failed: {e}")

        time.sleep(1)

    logger.info("TaskThread stopped")

# def trigger(did: str):
#     """Appelle fire(did=did) sur toutes les tâches enregistrées"""
#     with _lock:
#         for task in _tasks.values():
#             task.fire(did=did)

def sync(tid):
    if tid not in _tasks:
        logger.warning(f"TaskService: trying to force missing system {tid}")
        return


    task = _tasks[tid]
    with _lock:
        task.sync(Parameter.getDict(task.plugid))


def force(tid):
    if tid not in _tasks:
        logger.warning(f"TaskService: trying to force missing system {tid}")
        return

    with _lock:
        _tasks[tid].launch(utc=datetime.datetime.now(datetime.timezone.utc),did=None, force=True)


def register(task: Task):
    global _tasks

    if _running:
        raise TaskException("TaskService: trying to register system after start")

    if not isinstance(task, Task):
        raise TaskException("TaskService: trying to register a non Task object")

    if task.id is None:
        raise TaskException("TaskService: system musk have an id.")

    if task.id in _tasks:
        raise TaskException(f"TaskService: trying to register Task with existing id={task.id}")

    # On synchronize (ie on charge les paramètre depuis Parameter)

    #TODO: pas besoin ici ?
    #task.sync(Parameter.getAll(task.plugid))

    # On est bon
    _tasks[task.id] = task


def start():
    global _thread
    global _running

    _running = True
    # on démarre toutes les tâches

    for task in _tasks.values():
        task.start()

    # Lancement du thread principal
    _thread = threading.Thread(target=_run_thread, daemon=False)
    _thread.start()

    logger.info("TaskService started")


def stop():
    global _running
    # Arrête toutes les tâches
    _running = False

    for t in _tasks.values():
        t.stop()

    logger.info("TaskService stopped")


# def get(self,uid):
#     if uid in self._tasks:
#         return self._tasks[uid]
#     raise TaskException(f"TaskService: Task {uid} not found")

def dump():
    global _tasks
    print("--- TASKS -----------------------")
    for t in _tasks.values():
        print(t.plugid)
    print("---------------------------------")


def task_list():
    global _tasks
    res = []
    for uid, task in _tasks.items():
        res.append({
            "uid": uid,
            "period": task.period,
            "regex": task.regex,
            "last_trig": task.last_trig,
            "next_trig": task.next_trig,
            "plugid": task.plugid
        })
    return res


def task_list_with_parameter():
    tasks = task_list() # les taches
    #params = list(Parameter.select()) # les paramètres
    for t in tasks:
        # on récupère la liste des paramètres
        t["params"] = Parameter.getDict(t["plugid"])

    return tasks


def find(uid):
    global _tasks
    return _tasks.get(uid)  # or None
