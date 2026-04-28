# GYSMO

**G**eneric **Y**et **S**imple **M**onitoring **O**perator

## Configuration de Python 3

1. Mettez à jour l'index local des paquets : `sudo apt update`
2. Mettez à jour les paquets installés sur votre système : `sudo apt -y upgrade`
3. Installez **pip**, un outil qui installera et gérera les paquets de programmation : `sudo apt install -y python3-pip`
4. Configuration de votre environnement de programmation : `sudo apt install -y build-essential libssl-dev libffi-dev python3-dev`

## Configuration d'un environnement virtuel

Les environnements virtuels (`venv`) vous permettent d'avoir un espace isolé sur votre serveur pour les projets Python, garantissant que chacun de vos projets peut avoir son propre ensemble de dépendances qui ne perturbera pas les autres projets.

1. Installez **venv** : `sudo apt install -y python3-venv`
2. Créez un nouveau répertoire : `mkdir ENV` (dans le répertoire de travail actuel).
3. Accédez au répertoire de votre environnement de programmation : `cd /chemin/vers/ENV`
4. Créez un environnement virtuel pour votre projet : `python3 -m venv ENV`
5. Activez votre environnement virtuel : `source ENV/bin/activate`

## Install packages in Python using requirements.txt

1. `pip install -r requirements.txt`

## Configuration de l'appli

1. Copier le fichier `.env.to_fill` et le renomer en `.env`
2. Configurer le `.env`



## Test des mails en local (avec Docker)

1. `docker run --rm -it -p 3000:80 -p 26:25 rnwood/smtp4dev:v3`
2. `localhost:3000`

> En mode dev, le serveur est directement lancé sur le port 5001