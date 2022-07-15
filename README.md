# README
## Qualité du code

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Check%20Bandit?label=security)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Check%20Black?label=black)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Lint?label=lint)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Tests?label=tests)
![Codecov](https://img.shields.io/codecov/c/github/Netsach/concrete-datastore?logo=codecov)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![Python](https://img.shields.io/badge/python-3.6-3473A7?logo=python&logoColor=FED646)
![Python](https://img.shields.io/badge/python-3.7-3473A7?logo=python&logoColor=FED646)
![Python](https://img.shields.io/badge/python-3.8-3473A7?logo=python&logoColor=FED646)
![Python](https://img.shields.io/badge/python-3.9-3473A7?logo=python&logoColor=FED646)


## Description

`concrete-datastore` est un Datastore HTTP REST très polyvalent basé sur le framework Web [Django](https://djangoproject.com/).

Il est principalement utilisé comme serveur de base de données HTTP pour une application Web monopage (AWM).

Contrairement à un serveur de base de données classique tel que PostgreSQL ou MySQL où les requêtes sont effectuées à l'aide du langage SQL, chaque opération est effectuée à l'aide de requêtes HTTP simples.

`concrete-datastore` peut être considéré comme un serveur NoSQL ou comme une alternative à Firebase.

## Démarrage rapide

![Term sheet sample](https://concrete-datastore.netsach.org/en/latest/assets/mini-term-sample.svg)

```shell
git clone https://github.com/Netsach/concrete-datastore.git
cd concrete-datastore
docker run --name postgres-concrete-datastore -e POSTGRES_DB=db-concrete-datastore -e POSTGRES_USER=user-concrete-datastore -e POSTGRES_PASSWORD=pwd-concrete-datastore -d -p XXXX:5432 postgis/postgis:12-master
export POSTGRES_PORT=XXXX
export DATAMODEL_FILE=./docs/assets/sample-datamodel.yml
python3 -m venv env
source env/bin/activate
pip install -e ".[full]"
concrete-datastore makemigrations
concrete-datastore migrate
concrete-datastore createsuperuser
concrete-datastore runserver
```

Naviguez maintenant jusqu'à [http://127.0.0.1:8000/concrete-datastore-admin/](http://127.0.0.1:8000/concrete-datastore-admin/)

Vous pouvez maintenant créer un jeton pour utiliser l'API (ou utiliser le Endpoint d'authentification).

## Fonctionnalités

`concrete-datastore` est livré avec de nombreuses fonctionnalités intégrées telles que :

- Gestion des utilisateurs et des autorisations
- Backoffice généré automatiquement pour les administrateurs
- API entièrement REST utilisant JSON comme format de sérialisation
- Génération de statistiques simples
- Capacités d'envoi d'e-mails à partir de l'API
- ...

## Comment ça marche ?

Afin de décrire le schéma de la base de données, le développeur doit écrire un fichier `datamodel` en YAML ou JSON. Ce fichier `datamodel` permet à `concrete-datastore` de gérer la base de données sous-jacente à l'aide de PostgreSQL.

Chaque demande d'API est contrôlée par ce fichier `datamodel` car il agit comme une spécification de ce qui se trouve dans la base de données et de ce qui devrait être autorisé par chaque utilisateur.


Vous pouvez créer manuellement le fichier `datamodel` en suivant les exemples et la documentation ou utiliser l'éditeur en ligne [platform.concrete-datastore](https://platform.concrete-datastore.app/)

## F.A.Q

Si vous avez des questions, elles ont peut-être déjà été répondues dans le [FAQS.md](FAQS.md)

## Documentation officielle

Voir la [documentation officielle](http://concrete-datastore.netsach.org/)

## Version Anglaise

Vous pouvez retrouver la version Anglaise [ici](README-en.md)