# README

## Code Quality

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Check%20Bandit?label=security)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Check%20Black?label=black)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Lint?label=lint)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Netsach/concrete-datastore/Tests?label=tests)
![Codecov](https://img.shields.io/codecov/c/github/Netsach/concrete-datastore?logo=codecov)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)
![Python](https://img.shields.io/badge/python-3.6-3473A7?logo=python&logoColor=FED646)
![Python](https://img.shields.io/badge/python-3.7-3473A7?logo=python&logoColor=FED646)
![Python](https://img.shields.io/badge/python-3.8-3473A7?logo=python&logoColor=FED646)

## Description

`concrete-datastore` is a highly versatile HTTP REST Datastore based on the web framework [Django](https://djangoproject.com/).

It is used mainly as a HTTP database server for single page web application (SPA).

As opposed to a classic database server such as PostgreSQL or MySQL where queries are performed using SQL language, each operation is performed using plain HTTP requests. `concrete-datastore` abstracts the database layer.

`concrete-datastore` can be seen as a NoSQL server or as a Firebase alternative.

## Features

`concrete-datastore` comes with a lot of built-in features such as:

- User and permission management
- Automatically generated backoffice for administrators
- Fully REST API using JSON as serialization format
- Simple statistics generation
- Email sending capabilities from the API
- ...

## How does it work ?

In order to describe the database schema, the developer has to write a `datamodel` file in YAML or JSON. This `datamodel` file allows `concrete-datastore` to manage the underlying database using PostgreSQL.

Each API requests is controlled by this `datamodel` file as it acts as a specification of what is in the database and what should be allowed per user.

## Official documentation

See the [official documentation](http://concrete-datastore.netsach.org/)
