# Frequently Asked Questions

When you try out the `concrete-datastore` yourself, you might stumble across one of the following issues. We try to keep the list up to date. If you can not make it work or you find other impediments, please don't hesitate to contact us. We will try to find a solution and include it here.

## Table of Contents

<!-- MarkdownTOC autolink="true" -->

- [I do not have Docker installed](#i-do-not-have-docker-installed)
- [I do not have *virtualenv* installed](#i-do-not-have-virtualenv-installed)
- [I can not pip install: UNKNOWN error](#i-can-not-pip-install-unknown-error)
- [Running the migration scripts throws an error: role does not exists](#running-the-migration-scripts-throws-an-error-role-does-not-exists)
- [Troubleshooting Docker](#troubleshooting-docker)
- [How do I quit my virtualenv session?](#how-do-i-quit-my-virtualenv-session)
- [Is GDAL installed ?](#is-gdal-installed-)
<!-- /MarkdownTOC -->


## I do not have Docker installed
If you do not already have an PostgreSQL server running and you want to use docker, you need to download and install it. Please see the [official page](https://docs.docker.com/get-docker/) for more information.

## I do not have *virtualenv* installed
*virtualenv* is a useful tool that enables you to create isolated Python environments. Simply install it with *pip*:

``` shell
pip install virtualenv
```

## I can not pip install: UNKNOWN error

When running the `pip install -e ".[full]"` you might see the following (wrong) output:

``` shell
UNKNOWN 0.0.0 does not provide the extra 'full'
Installing collected packages: UNKNOWN
  Found existing installation: UNKNOWN 0.0.0
    Uninstalling UNKNOWN-0.0.0:
      Successfully uninstalled UNKNOWN-0.0.0
  Running setup.py develop for UNKNOWN
Successfully installed UNKNOWN
```

This is not expected. To solve this, please upgrade *pip* and the *setuptools* as follows:

```shell
pip install --upgrade pip
pip install setuptools --upgrade
```

## Running the migration scripts throws an error: role does not exists
If you get an error like the following:
``` shell
django.db.utils.OperationalError: FATAL:  role "user-concrete-datastore" does not exist
```

You used the wrong run command for docker. The container might not even be started, or it crashed right after the launch. This is due to the fact that a database name, username and password is required. If you are just trying out the `concrete-datastore`, use the following default settings:

```shell
docker run --name postgres-concrete-datastore -e POSTGRES_DB=db-concrete-datastore -e POSTGRES_USER=user-concrete-datastore -e POSTGRES_PASSWORD=pwd-concrete-datastore -d -p 5432:5432 postgres
```

Afterwards, you should be able to run the following commands.

## Troubleshooting Docker
To see all containers, use:

```shell
docker ps -a
```

To show only the running containers, use:
```shell
docker ps
```

If a container did not start, or you suspect problems, check the logs:

```shell
docker container logs <container_id>
```

To stop and remove a running container, use:
```shell
docker kill <container_id>
docker rm <container_id>
```

## How do I quit my virtualenv session?
If you are done working with the virtual environment, just deactivate it by running:

``` shell
deactivate
```

## Is GDAL installed ?
### For MacOS
If your terminal prints an error like : ```Could not find the GDAL library ... is GDAL installed``` try to run ```brew install gdal``` in your shell. (N.B : this command requires to have Xcode installed on your Mac)
If this doesn't fix your issue, try :
```shell
brew install PostgreSQL
brew install postgis
```

### For Linux
If your terminal prints an error like : ```Could not find the GDAL library ... is GDAL installed``` try to run in your terminal :
```shell
sudo apt-get install gdal-bin
``` 
