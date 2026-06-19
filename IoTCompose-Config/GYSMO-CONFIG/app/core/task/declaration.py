import datetime
import logging
import re



class TaskException(Exception):
    pass

class Task:

    def __init__(self, id, plugid: "Str"):

        # L'identifiant de la tache (souvent "PLUGIN-task")
        self._id = id

        # L'identifiant du plugin (souvent "PLUGIN")
        self._plugid = plugid
        #
        self._last_trigger = None # instant du dernier déclenchement
        self._next_trigger = None # l'instant du prochain instant de déclenchement..

        # Gestion du déclenchement
        self._task_regex = []  # Liste des regex de déclenchement
        self._task_period = 0  # périodicité de déclenchement (en seconde ?) SI 0 => ARRET



    @property
    def id(self):
        return self._id

    @property
    def plugid(self):
        return self._plugid

    # @uid.setter
    # def uid(self,uid):
    #     if self._uid is not None:
    #         raise TaskException(f"TaskService: trying to rename system {self._uid}")
    #     self._uid = uid

    @property
    def last_trig(self):
        return self._last_trigger

    @property
    def next_trig(self):
        return self._next_trigger


    def add_regex(self, str):
        regex = re.compile(str)
        self._task_regex.append(regex)

    def set_period(self, period):
        self._task_period = period

    def sync(self, params):
        """Auto-configuration à partir des données contenues dans le dictinnaire params"""
        pass
    
    def start(self):
        pass

    def stop(self):
        pass

    def fire(self, did = None, force = False) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc) #On récupère la date en local
        ok = False
        if force:
            # on déclenche inconditionnellement
            ok = True
        else:
            if did is not None: # on vérifie le déclenchement via le regex si string existe
                for r in self._task_regex:
                    if r.search(did):
                        ok = True
            # et on déclenche le cas échéant avec le période
            ok |= (self._next_trigger is None) or now >= self._next_trigger
        
        return ok

    def launch(self,utc,did,force):
        # Exécution 
        self.execute(utc,did,force)
        # Planification
        self._last_trigger = utc
        if not force and self._task_period>0:
            # On planifie
            self._next_trigger = utc + datetime.timedelta(seconds=self._task_period)

    def execute(self,time,did,force):
        # time -> l'instant courant
        # did -> l'identifiant de la donnée qui a déclenché le traitement
        # force -> est-ce un déclenchement forcé ?
        raise TaskException("Task is an abstract class -> Requires inheritance")


    @property
    def period(self):
        return self._task_period

    @property
    def regex(self):
        return ",".join([str(r) for r in self._task_regex])

