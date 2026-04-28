import datetime
from dateutil.relativedelta import relativedelta
import logging
import secrets
from threading import Thread

import dotenv
from flask import Flask, render_template, Blueprint, url_for, request
from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from werkzeug.routing import BuildError

from core.plugin import Plugin

dotenv.load_dotenv()  # Chargement des variables d'environnement
logger = logging.getLogger(__name__)

logger.info("Initializing Web Service")

# Variable qui porte les entrées du menu
_menu = {}  # Dictionnaire qui dont la clé est le nom et la valeur l'url

app = None
_thread = None
_blueprints = []

# #####################################################
# Déclaration et configuration de l'App Flask
# #####################################################
app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap5(app, )
#moment = Moment(app)

csrf = CSRFProtect(app)


# #####################################################
# Déclaration des fonctions annexes
# #####################################################


def dynamic_url_for(route_name, *args, **kwargs):
    return url_for(route_name.replace('%', request.blueprint), *args, **kwargs)


# def dynamic_url_for(route_name, *args, **kwargs):
#    try:
#        url = url_for(f"{request.blueprint}.{route_name}", *args, **kwargs)
#        return url
#    except BuildError as e:
#        logger.debug(f"[WEB] Route '{route_name}' doesn't exist. Returning '#'.")
#        return "#"
# Pour permettre la génération de la page même lorsqu'une route n'est pas définie

def dynamic_url_or_hash_for(route_name):
    try:
        url = dynamic_url_for(route_name)
        return url
    except BuildError:
        logger.debug(f"[WEB] Route '{route_name}' doesn't exist. Returning '#'.")
        return "#"


# Ajouter la fonction comme une fonction globale pour qu'elle soit accessible depuis les modèles
app.add_template_global(dynamic_url_or_hash_for, 'dynamic_url_or_hash_for')
app.add_template_global(dynamic_url_for, 'dynamic_url_for')

# Gestion du formatage des dates et heures

@app.template_filter("format")
def format(value, format="%d/%m/%Y %H:%M:%S"):
    return value.strftime(format) if isinstance(value, datetime.datetime) else ""

@app.template_filter("elapsed")
def elapsed(value, format="%d/%m/%Y %H:%M:%S"):
    now = datetime.datetime.now()
    delta = relativedelta(now, value)
    parts = []
    if delta.years:
        parts.append(f"{delta.years} a")
    if delta.months:
        parts.append(f"{delta.months} m")
    if delta.days:
        parts.append(f"{delta.days} j")
    if delta.hours:
        parts.append(f"{delta.hours} h")
    if delta.minutes:
        parts.append(f"{delta.minutes} min")
    if delta.seconds:
        parts.append(f"{delta.seconds} s")

    return " ".join(parts)


@app.context_processor
def inject_global_variable():
    global _menu
    # Vous pouvez définir la valeur de votre variable ici
    ts = datetime.datetime.now()

    # l'identifiant du plugins
    pid = request.blueprint or ""
    return {"__ts__": ts, "__pid__": pid, "__menu__": _menu}


@app.errorhandler(404)
def _handle_404_error(ex):
    return render_template("404.html", ex=ex)


@app.errorhandler(406)
def _handle_406_error(ex):
    return render_template("406.html", ex=ex)


@app.before_request
def add_plugid_to_request():
    # Ajouter dynamiquement un nouvel attribut à l'objet request
    request.plugid = request.blueprint


def start(prod=True):
    global _thread
    if prod:
        fun = _prod_run_thread
    else:
        fun = _dev_run_thread

    _thread = Thread(target=fun, daemon=True)
    _thread.start()
    logger.info("Web service started")


def stop():
    logger.info("Web service stopped")


def _dev_run_thread():
    global app
    app.run(host="0.0.0.0", port=8080, debug=True,
            use_reloader=False)  # Les deux arguments sont nécessaires pour que le therad fonctionne


def _prod_run_thread():
    global app
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080, threads=8)


def load(webapp: Blueprint, plugin: Plugin):
    global app
    global _blueprint
    global _menu

    if not plugin.prefix.startswith("/"):
        prefix = f'/{plugin.prefix}'

    # if webapp.name != plugin.uid:
    #     logger.info(f"Renaming webapp {webapp.name} -> {plugin.uid}")
    #     webapp.name = plugin.uid
    #
    if plugin.pid in _blueprints:
        logger.warning(f"Blueprint {plugin.pid} already registered")
        return

    if plugin.menu_name is not None:
        _menu[plugin.menu_name] = plugin.prefix

    app.register_blueprint(webapp, url_prefix=plugin.prefix)


def load_webapps(self, path):
    pass
    # root = os.path.join(os.getcwd(), path)
    # print(root)
    #
    # base = ".".join(path.split("/"))
    # print(base)
    #
    # # On charge les webapp principale
    # dirs = glob.glob(f'{root}/*/', recursive=False)
    #
    # # Affichez la liste des répertoires
    # for path in dirs:
    #     print(f"On traite {path}")
    #     if "__pycache__" in path:  # Pour éviter les pycache en particulier...
    #         continue
    #
    #     # on doit récupérer le chemin relatif pour pouvoir construire le nom du package à charger
    #     rel = os.path.relpath(path, start=root)
    #     rel_base = ".".join(rel.split("/"))
    #     package = importlib.import_module(f"{base}.{rel_base}")
    #     logger.info(f"Registering wepapp {package.webapp.name}")
    #
    #     url_prefix = "/"
    #     if package.webapp.name != "welcome":
    #         url_prefix = f"/{package.webapp.name}"
    #
    #     self._app.register_blueprint(package.webapp, url_prefix=url_prefix)


# =============================================================================================================
# Déclaration des routes et autre
# =============================================================================================================
#
# def _delete_route_containing(self, prefix):
#     while True:
#         rule = next(r for r in self._app.url_map.iter_rules() if prefix in r.endpoint)
#         if rule is None:
#             break
#         self._app.url_map._rules.remove(rule)

def dump():
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"{rule.endpoint}: {rule} [{methods}]")

# _configure()
