#: coding: utf-8
from django.conf import settings
from django.core.management.base import BaseCommand
from concrete_datastore.concrete import models as concrete_models


def get_sorted_stats(key):
    data_model = settings.META_MODEL_DEFINITIONS
    models = data_model['manifest']['data_modeling']['models']
    model_names = map(lambda x: x['name'], models)
    models_count = [
        {'name': name, 'count': getattr(concrete_models, name).objects.count()}
        for name in model_names
    ]
    reverse = key.startswith('-')
    return sorted(
        models_count, key=lambda x: x[key.replace('-', '')], reverse=reverse
    )


class Command(BaseCommand):
    help = 'Displays a list of all models and the number of instances in DB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            type=str,
            help=(
                'The key used to sort the display: * "name": the result will '
                'be sorted by ascending based on the model name * "-name": '
                'the result will be sorted by descending based on the model '
                'name * "count": the result will be sorted by ascending based '
                'on the number of instances * "-count": the result will be '
                'sorted by descending based on the number of instances'
            ),
            choices=('name', 'count', '-name', '-count'),
            default='-count',
        )

    def handle(self, *args, **options):
        key = options['key']
        for elt in get_sorted_stats(key=key):
            print(f'{elt["name"]}: {elt["count"]:_} objetcs')
