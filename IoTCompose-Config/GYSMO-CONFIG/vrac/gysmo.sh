#!/bin/bash

# Le nom du script Python à lancer ou arrêter
SCRIPT="gysmo.py"

# Récupérer l'option passée en paramètre
ACTION=$1

# Charger les variables d'environnement depuis le fichier .env
if [ -f .env ]; then
    source .env
    echo "Variables d'environnement chargées depuis .env"
else
    echo "Le fichier .env est introuvable."
    exit 1
fi

# Vérifier que VENV_PATH est bien défini
if [ -z "$VENV_PATH" ]; then
    echo "La variable VENV_PATH n'est pas définie dans .env."
    exit 1
fi

# Vérifier si le virtualenv est activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtualenv non activé. Activation du virtualenv..."
    # Activer le virtualenv
    source "$VENV_PATH/bin/activate"
    if [ $? -ne 0 ]; then
        echo "Échec de l'activation du virtualenv."
        exit 1
    fi
else
    echo "Virtualenv déjà activé : $VIRTUAL_ENV"
fi


# Vérifier si le script est déjà en cours d'exécution
pid=$(ps aux | grep "$SCRIPT" | grep -v 'grep' | awk '{print $2}')

# Fonction pour démarrer le script
start_script() {
    if [ -z "$pid" ]; then
        # Le processus n'est pas en cours, on peut le lancer
        echo "Lancement de $SCRIPT..."
        python "$SCRIPT" &
        echo "$SCRIPT lancé en arrière-plan."
    else
        # Le processus est déjà en cours
        echo "$SCRIPT est déjà en cours d'exécution."
    fi
}

# Fonction pour arrêter le script
stop_script() {
    if [ -z "$pid" ]; then
        # Le processus n'est pas en cours, rien à faire
        echo "$SCRIPT n'est pas en cours d'exécution."
    else
        # Le processus est en cours, on l'arrête
        echo "Arrêt du processus $SCRIPT (PID: $pid)..."
        kill -SIGTERM "$pid"

        # Attendre que le processus se termine
        while kill -0 "$pid" 2>/dev/null; do
            echo "Le processus $SCRIPT est toujours en cours..."
            sleep 1
        done

        echo "$SCRIPT a été arrêté."
    fi
}

# Fonction pour redémarrer le script
restart_script() {
    if [ -z "$pid" ]; then
        # Le processus n'est pas en cours, on peut simplement démarrer
        echo "$SCRIPT n'est pas en cours d'exécution, lancement de $SCRIPT..."
        python "$SCRIPT" &
        echo "$SCRIPT lancé."
    else
        # Le processus est déjà en cours, on l'arrête et on le relance
        echo "Redémarrage de $SCRIPT..."
        kill -SIGTERM "$pid"

        # Attendre que le processus se termine
        while kill -0 "$pid" 2>/dev/null; do
            echo "Le processus $SCRIPT est toujours en cours..."
            sleep 1
        done

        echo "$SCRIPT a été arrêté. Relance de $SCRIPT..."
        python "$SCRIPT" &
        echo "$SCRIPT relancé."
    fi
}

# Vérifier l'argument et exécuter l'action correspondante
case "$ACTION" in
    START)
        start_script
        ;;
    STOP)
        stop_script
        ;;
    RESTART)
        restart_script
        ;;
    *)
        echo "Usage: $0 {START|STOP|RESTART}"
        exit 1
        ;;
esac
