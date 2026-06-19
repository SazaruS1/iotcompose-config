# Par convention, le nom "_ROOT_" sera monté sur la racine
from datetime import datetime

from flask import Blueprint, render_template

import core.datastore.service as ds
from core.models import Device

webapp = Blueprint("__MUST_BE_CHANGED__", __name__, template_folder="views")

@webapp.route('/')
def index():
    return render_template("virtual-sinus/index.html")

