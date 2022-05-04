# coding: utf-8
from django.test import TestCase
import json
from concrete_datastore.concrete.models import User
from django.test import Client
from tests.utils import create_an_user_and_get_token
from django.test import override_settings


@override_settings(DEBUG=True)
class FixBug79Test(TestCase):
    """
    1/ Create a simple user and Get token
    2/ Patch this user (change `last_name`)

    il y a une incohérence débile entre manager et is_staff dans concrete

    un coup c'est l'un un coup c'est l'autre

    le user est simple user

    il essaye de s'updater lui-même sur un champ custom

    options.get('level', 'superuser')

    """

    def test_set_get_level_api_v1_0(self):
        self._test_set_get_level(api_version='1', is_public=False)

    def test_set_get_level_api_v1_1(self):
        self._test_set_get_level(api_version='1.1', is_public=False)

    def test_set_get_level_api_v1_0_public(self):
        self._test_set_get_level(api_version='1', is_public=True)

    def test_set_get_level_api_v1_1_public(self):
        self._test_set_get_level(api_version='1.1', is_public=True)

    def _test_set_get_level(self, api_version, is_public=False):
        user, token = create_an_user_and_get_token(
            options={'level': 'simpleuser', 'is_public': is_public},
            api_version=api_version,
        )

        self.assertEqual(user.public, is_public)

        user_url = '/api/v{}/user/{}/'.format(api_version, user.uid)

        client = Client(HTTP_AUTHORIZATION='Token {}'.format(token))
        response = client.get('/api/v{}/user/'.format(api_version))

        # This test is obsolete. Any action on /user/
        # by a simpleuser is forbidden
        self.assertEqual(response.status_code, 403)

        response = client.patch(
            user_url,
            json.dumps({'last_name': 'balek'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
