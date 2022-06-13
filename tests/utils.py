# coding: utf-8
import uuid
from django.test import Client
from concrete_datastore.concrete.models import User, UserConfirmation, Village


def create_an_user_and_get_token(options=None, api_version='1'):
    if options is None:
        options = {}

    email = options.get('email', 'johndoe@netsach.org')
    password = options.get('password', uuid.uuid4().hex)
    level = options.get('level', 'superuser')

    user = User.objects.create_user(email)
    user.public = options.get('is_public', False)
    user.set_level(level, commit=False)
    user.set_password(password)
    user.save()

    UserConfirmation.objects.create(user=user, confirmed=True)

    url = '/api/v{}/auth/login/'.format(api_version)
    resp = Client().post(url, {"email": email, "password": password})
    token = resp.data['token']
    return user, token


class TestRegisterBackend:
    def post_register(self, request, user, *args, **kwargs):
        #: set the level to manager
        user.set_level('manager')
        user.save()

    def pre_register(self, request, *args, **kwargs):
        #: delete all instances of model Village
        Village.objects.all().delete()
