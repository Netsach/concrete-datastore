import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "concrete_datastore.settings.development"
)
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
