import json
from datetime import datetime

def as_bool(var):
    if type(var) is bool:
        return var

    # On transforme en chaine
    var = str(var).lower()

    return True if var == 'true' else False


def safe_int(string, val=None):
    if string is None:
        return val

    try:
        return int(string)
    except ValueError:
        return val


def safe_float(string, val=None):
    if string is None:
        return val

    try:
        return float(string)
    except ValueError:
        return val


def format_json(data):
    def custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    return json.dumps(data, indent=4, ensure_ascii=False, default=custom_serializer)


def sanitize(val):
    # ON conserve " comme délimiteur de chaine dans les requêtes...
    if isinstance(val, str):
        val = val.replace('"', "'")  # On supprime les " dans les textes
        val = f'"{val}"'
    elif isinstance(val, datetime):
        val = f'"{val}"'
    elif isinstance(val, bool):
        val = "true" if val else "false"
    elif val is None:
        val = 'NULL'
    else:
        val = str(val)

    return val


import os
import hashlib


def _hash_file(path, algorithm='sha256', bloc_size=65536):
    """
    Calcule le hash d'un fichier en utilisant l'algorithm spécifié.
    """
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as fichier:
        bloc = fichier.read(bloc_size)
        while len(bloc) > 0:
            hasher.update(bloc)
            bloc = fichier.read(bloc_size)
    return hasher.hexdigest()


def hash_recursive(root, algorithm='sha256', bloc_size=65536):
    """
    Calcule le hash de tous les fichiers dans l'arborescence spécifiée.
    """
    hasher = hashlib.new(algorithm)

    for path, subpath, files in os.walk(root):
        for filename in files:
            filepath = os.path.join(path, filename)
            with open(filepath, 'rb') as f:
                bloc = f.read(bloc_size)
                while len(bloc) > 0:
                    hasher.update(bloc)
                    bloc = f.read(bloc_size)

    return hasher.hexdigest()


if __name__ == "__main__":
    # TEST
    chemin_repertoire = '../plugins/test_plugin'

