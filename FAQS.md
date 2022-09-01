# Questions fréquemment posées

Lorsque vous essayez vous-même `concrete-datastore`, vous pouvez rencontrer l'un des problèmes suivants. Nous essayons de tenir la liste à jour. Si vous ne pouvez pas le faire fonctionner ou si vous rencontrez d'autres obstacles, n'hésitez pas à nous contacter. Nous allons essayer de trouver une solution et de l'inclure ici.

## Table des matières

<!-- MarkdownTOC autolink="true" -->

- [Je n'ai pas installé Docker](#je-n'ai-pas-installé-Docker)
- [Je n'ai pas *virtualenv* installé](#je-n'ai-pas-virtualenv-installé)
- [Je n'arrive pas à installer pip : erreur INCONNUE](#je-n'arrive-pas-à-installer-pip-erreur-inconnue)
- [L'exécution des scripts de migration génère une erreur : le rôle n'existe pas](#running-the-migration-scripts-throws-an-error-role-does-not-exists)
- [Dépannage Docker](#dépannage-docker)
- [Comment quitter ma session virtualenv ?](#comment-quitter-ma-session-virtualenv)
- [GDAL est-il installé ?](#gdal-est-il-installé)
<!-- /MarkdownTOC -->


## Je n'ai pas installé Docker
Si vous n'avez pas encore de serveur PostgreSQL en cours d'exécution et que vous souhaitez utiliser docker, vous devez le télécharger et l'installer. Veuillez consulter la [page officielle](https://docs.docker.com/get-docker/) pour plus d'informations.

## Je n'ai pas *virtualenv* installé
*virtualenv* est un outil utile qui vous permet de créer des environnements Python isolés. Installez-le simplement avec *pip*:

``` shell
pip install virtualenv
```

## Je n'arrive pas à installer pip : erreur INCONNUE

Lors de l'exécution de `pip install -e ".[full]"`, vous pouvez voir la sortie suivante (erronée) :

``` shell
UNKNOWN 0.0.0 does not provide the extra 'full'
Installing collected packages: UNKNOWN
  Found existing installation: UNKNOWN 0.0.0
    Uninstalling UNKNOWN-0.0.0:
      Successfully uninstalled UNKNOWN-0.0.0
  Running setup.py develop for UNKNOWN
Successfully installed UNKNOWN
```

Ceci n'est pas l'attendu. Pour résoudre ce problème, veuillez mettre à jour *pip* et les *setuptools* comme indiqué ici :

```shell
pip install --upgrade pip
pip install setuptools --upgrade
```

## L'exécution des scripts de migration génère une erreur : le rôle n'existe pas
Si vous obtenez une erreur comme celle-ci :
``` shell
django.db.utils.OperationalError: FATAL:  role "user-concrete-datastore" does not exist
```

Vous avez utilisé la mauvaise commande d'exécution pour docker. Le conteneur peut même ne pas être démarré, ou il s'est écrasé juste après le lancement. Cela est dû au fait qu'un nom de base de données, un nom d'utilisateur et un mot de passe sont requis. Si vous essayez juste le `concrete-datastore`, utilisez les paramètres par défaut suivants :

```shell
docker run --name postgres-concrete-datastore -e POSTGRES_DB=db-concrete-datastore -e POSTGRES_USER=user-concrete-datastore -e POSTGRES_PASSWORD=pwd-concrete-datastore -d -p 5432:5432 postgres
```

Ensuite, vous devriez pouvoir exécuter les commandes suivantes.

## Dépannage Docker
Pour voir tous les conteneurs, utilisez :

```shell
docker ps -a
```

Pour afficher uniquement les conteneurs en cours d'exécution, utilisez :
```shell
docker ps
```

Si un conteneur n'a pas démarré ou si vous soupçonnez des problèmes, consultez les journaux :

```shell
docker container logs <container_id>
```

Pour arrêter et supprimer un conteneur en cours d'exécution, utilisez :
```shell
docker kill <container_id>
docker rm <container_id>
```

## Comment quitter ma session virtualenv ?
Si vous avez fini de travailler avec l'environnement virtuel, il suffit de le désactiver en exécutant :

``` shell
deactivate
```

## GDAL est-il installé ?
### Pour MacOS
Si votre terminal affiche une erreur du type : ```Could not find the GDAL library ... is GDAL installed``` essayez d'exécuter ```brew install gdal``` dans votre shell. (N.B : cette commande nécessite d'avoir Xcode installé sur votre Mac)
Si cela ne résout pas votre problème, essayez :
```shell
brew install PostgreSQL
brew install postgis
```

### Pour Linux
Si votre terminal affiche une erreur du type : ```Could not find the GDAL library ... is GDAL installed``` essayez d'exécuter dans votre terminal :
```shell
sudo apt-get install gdal-bin
``` 

## Version Anglaise

Vous pouvez retrouver la version Anglaise [ici](FAQS-en.md).