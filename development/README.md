# Development

## Configure the environment

```shell
python3 -m venv env
source env/bin/activate
pip install -e ".[full]"
```

## Run redis

```shell
docker run --name redis-concrete-datastore -d -v `pwd`/containers/redis:/ns-shared-data -p 6379:6379 redis
```

## Run the web app

```shell
export BROKER_URL=redis://localhost:6379/0
django runserver
```

## Launch Celery tasks

```shell
export DJANGO_SETTINGS_MODULE=development.settings
export BROKER_URL=redis://localhost:6379/0
celery -A concrete_datastore.settings.celery worker -l info --beat --concurrency 1 --queues=celery,periodic,plugin_tasks
```
