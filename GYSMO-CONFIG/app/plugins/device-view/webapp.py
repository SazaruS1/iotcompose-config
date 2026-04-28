# Par convention, le nom "_ROOT_" sera monté sur la racine
import csv
import io
import zipfile
from datetime import datetime, timedelta
from os import device_encoding

import numpy as np
from flask import Blueprint, render_template, abort, request, Response, send_file

import core.datastore.service as interface
from core.models import Device, Record

webapp = Blueprint("__MUST_BE_CHANGED__", __name__, template_folder="views")

@webapp.route('/')
def index():

    query = Device.select().where(Device.name.is_null(False)).namedtuples()
    devices = list(query)

    #data = interface.pull()
    return render_template("device-view/index.html",devices=devices)

@webapp.route('/export')
def export():
    # on récupère la liste des capteurs utiles
    query = Device.select().where(Device.name.is_null(False)).namedtuples()
    devices = list(query)

    #data = interface.pull()
    return render_template("device-view/export.html",devices=devices)


@webapp.route('/download', methods=['POST'])
def download():

    print("ici")
    data = request.get_json()

    if data['stop'] is None  or data['stop'] == "":
        stop = datetime.now()
    else:
        stop = datetime.fromisoformat(data['stop'])

    if data['start'] is None  or data['start'] == "":
        start = stop-timedelta(hours=12)
    else:
        start = datetime.fromisoformat(data['start'])

    # if data['dt'] is None  or data['dt'] == "":
    #     dt = 60
    # else:
    #     dt = float(data['dt'])  # en secondes

    uids = data['uids']     # liste de strings

    if start > stop:
        start, stop =  stop, start # on permute


    # Création de l'archive
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Pour chaque UID demandé
        for uid in uids:
            dev = Device.get_or_none(Device.uid == uid)
            if dev is None:
                continue  # skip uid invalide

            # Récupère les enregistrements filtrés par période
            query = (
                Record
                .select(Record.ts, Record.value)
                .where(
                    (Record.device == dev) &
                    (Record.ts >= start) &
                    (Record.ts <= stop)
                )
                .order_by(Record.ts)
            )

            # Construit le contenu du fichier texte
            lines = [f"{r.ts.isoformat()}\t{r.value}\t{'G->D' if r.action else 'D->G'}" for r in query]
            content = "\n".join(lines)

            # Nom du fichier (name.txt)
            filename = f"{dev.name or dev.uid}.txt"

            # Ajout au zip
            zipf.writestr(filename, content)

    memory_file.seek(0)

    return send_file(
        memory_file,
        as_attachment=True,
        download_name="records_export.zip",
        mimetype="application/zip"
    )


@webapp.route('/graph/<int:pk>',methods=['GET'])
def graph(pk):
    # On récupère le device s'il exist
    device = Device.get_or_none(pk)
    if device is None:
        abort(406)

    # On récupère les paramètres éventuels de debut et fin
    # Récupération des paramètres de requête 'start_date' et 'stop_date'
    start_date_str = request.args.get('start')  # Ex: "2024-09-01"
    stop_date_str = request.args.get('stop')  # Ex: "2024-09-06"

    # Initialisation des variables de date avec None
    start_date = None
    stop_date = None

    # Conversion des chaînes de caractères en objets datetime
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass

    if stop_date_str:
        try:
            stop_date = datetime.strptime(stop_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass

    if not stop_date_str:
        stop_date = datetime.now()

    if not start_date_str:
        start_date = stop_date - timedelta(days=1)

    query = Record.select(Record.ts, Record.value, Record.action).where(Record.device == device)
    query = query.where(Record.ts >= start_date)
    query = query.where(Record.ts <= stop_date)
    query = query.order_by(Record.ts.asc())

    x = [r.ts.isoformat() for r in query]  # Convertir datetime en chaîne
    yd = [r.value if not r.action else None for r in query ]  #
    ya = [r.value if r.action else None for r in query ]  #

    return render_template("device-view/graph.html",data = {'x': x, 'yd': yd, "ya":ya}, name=f"{device.name} [{device.unit}]", start_date=start_date, stop_date=stop_date)


@webapp.route('/table/<int:pk>',methods=['GET'])
def table(pk):
    # On récupère le device s'il exist
    device = Device.get_or_none(pk)
    if device is None:
        abort(406)

    query = Record.select(Record.ts, Record.value, Record.action).where(Record.device == device)
    query = query.order_by(Record.ts.desc())
    query.limit(100)  # Limitation à N lignes

    data = list(query.dicts())


    return render_template("device-view/table.html",data = data)
