# Lancement avec Docker

Attention:

- Nécessite l'installation de Docker
- ne pas oublier de mettre le `.env`

## Commandes de base

- Lancer le système : `docker-compose up -d --build` (dans le répertoire de Gysmo ie au même niveau que `docker-compose.yml`)
    - L'application doit être accessible sur (http://localhost:8080)
    - L'option `--build` permet de construire l'image. Elle n'est utile que la première fois
    - l'option `-d` permet de "détacher" l'exécution du container qui tournera en tâche de fond.

- Pour consulter les traces de l'application : `docker logs gysmo`
- Pour lancer un shell dans le container : `docker exec -it gysmo bash`
- Pour arrêter le système: `docker-compose down`