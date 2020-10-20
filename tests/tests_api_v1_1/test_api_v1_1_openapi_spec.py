# coding: utf-8
from django.test import override_settings
from django.core.management import call_command
from django.core.exceptions import PermissionDenied
from django.core.management.base import CommandError
from rest_framework.test import APITestCase
from rest_framework import status

from concrete_datastore.concrete.models import User, UserConfirmation

from io import StringIO
import yaml
import json


@override_settings(DEBUG=True)
class TestOpenAPISchemaCommand(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.is_superuser = True
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.simpleuser = User.objects.create_user('simpleuser@netsach.org')
        self.simpleuser.set_password('plop')
        self.simpleuser.set_level('simpleuser')
        self.simpleuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.simpleuser, confirmed=True
        ).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "simpleuser@netsach.org", "password": "plop"}
        )
        self.simpletoken = resp.data['token']

    def test_openapispec_yaml_command(self):
        out = StringIO()
        call_command("openapispec", stdout=out)
        yaml_resp = yaml.load(out.getvalue(), Loader=yaml.FullLoader)
        self.assertIn('openapi', yaml_resp)
        self.assertIn('info', yaml_resp)
        self.assertIn('security', yaml_resp)
        self.assertIn('paths', yaml_resp)
        self.assertIn('components', yaml_resp)

        self.assertNotIn('servers', yaml_resp)
        self.assertEqual(yaml_resp['openapi'], '3.0.2')

    def test_openapispec_json_command(self):
        out = StringIO()
        opts = {'format': 'json'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('openapi', json_resp)
        self.assertIn('info', json_resp)
        self.assertIn('security', json_resp)
        self.assertIn('paths', json_resp)
        self.assertIn('components', json_resp)

        self.assertFalse('servers' in json_resp)
        self.assertEqual(json_resp['openapi'], '3.0.2')

    def test_openapispec_json_command_with_servers(self):
        out = StringIO()
        opts = {'format': 'json', 'servers': '["http://test-server.com"]'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('openapi', json_resp)
        self.assertIn('info', json_resp)
        self.assertIn('security', json_resp)
        self.assertIn('paths', json_resp)
        self.assertIn('components', json_resp)
        self.assertIn('servers', json_resp)

        self.assertEqual(json_resp['openapi'], '3.0.2')
        self.assertEqual(
            json_resp['servers'], [{'url': 'http://test-server.com'}]
        )

    def test_openapispec_json_command_permissions_with_db(self):
        """
            Model Crud has minimum_level to admin
            SuperUser can access the endpoint /crud/ from the generated spec
            SimpleUser and AnonymousUser can't access the endpoint /crud/
        """
        #:  SuperUser
        out = StringIO()
        opts = {'format': 'json', 'token': self.token}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertTrue('/api/v1.1/crud/' in json_resp['paths'])

        #:  SimpleUser
        out = StringIO()
        opts = {'format': 'json', 'token': self.simpletoken}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertNotIn('/api/v1.1/crud/', json_resp['paths'])

        #:  Invalid token
        out = StringIO()
        opts = {'format': 'json', 'token': 'FAKE_TOKEN'}
        with self.assertRaises(PermissionDenied):
            call_command("openapispec", **opts, stdout=out)

    def test_openapispec_command_with_wrong_options(self):
        #:  Wrong user_level:
        out = StringIO()
        opts = {'format': 'json', 'level': 'invalid_level'}
        with self.assertRaises(CommandError):
            call_command("openapispec", **opts, stdout=out)

        #:  Wrong format:
        out = StringIO()
        opts = {'format': 'wrong_format', 'level': 'simpleuser'}
        with self.assertRaises(CommandError):
            call_command("openapispec", **opts, stdout=out)

        #:  Wrong api_version:
        out = StringIO()
        opts = {'format': 'json', 'api_version': 'wrong_api_version'}
        with self.assertRaises(CommandError):
            call_command("openapispec", **opts, stdout=out)

    def test_openapispec_json_command_permissions_without_db(self):
        """
            Model Crud has minimum_level to admin
            SuperUser can access the endpoint /crud/ from the generated spec
            SimpleUser and AnonymousUser can't access the endpoint /crud/
        """
        #:  SuperUser
        out = StringIO()
        opts = {'format': 'json', 'level': 'superuser'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertIn('/api/v1.1/crud/', json_resp['paths'])

        #:  Admin
        out = StringIO()
        opts = {'format': 'json', 'level': 'admin'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertIn('/api/v1.1/crud/', json_resp['paths'])

        #:  SimpleUser
        out = StringIO()
        opts = {'format': 'json', 'level': 'simpleuser'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertNotIn('/api/v1.1/crud/', json_resp['paths'])

        #:  Anonymous
        out = StringIO()
        opts = {'format': 'json'}
        call_command("openapispec", **opts, stdout=out)
        json_resp = json.loads(out.getvalue())
        self.assertIn('paths', json_resp)
        self.assertNotIn('/api/v1.1/crud/', json_resp['paths'])


@override_settings(DEBUG=True)
class TestOpenAPISchemaView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.is_superuser = True
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.simpleuser = User.objects.create_user('simpleuser@netsach.org')
        self.simpleuser.set_password('plop')
        self.simpleuser.set_level('simpleuser')
        self.simpleuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.simpleuser, confirmed=True
        ).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "simpleuser@netsach.org", "password": "plop"}
        )
        self.simpletoken = resp.data['token']

    def test_json_spec(self):
        get_url = '/openapi-schema.json'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION=f'Token {self.token}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('openapi', json_resp)
        self.assertIn('info', json_resp)
        self.assertIn('servers', json_resp)
        self.assertIn('security', json_resp)
        self.assertIn('paths', json_resp)
        self.assertIn('components', json_resp)

        self.assertEqual(json_resp['openapi'], '3.0.2')

    def test_yaml_spec(self):
        get_url = '/openapi-schema.yaml'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION=f'Token {self.token}'
        )

        yaml_resp = yaml.load(resp.content, Loader=yaml.FullLoader)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('openapi', yaml_resp)
        self.assertIn('info', yaml_resp)
        self.assertIn('servers', yaml_resp)
        self.assertIn('security', yaml_resp)
        self.assertIn('paths', yaml_resp)
        self.assertIn('components', yaml_resp)

        self.assertEqual(yaml_resp['openapi'], '3.0.2')

    @override_settings(OPENAPI_SPEC_TITLE='SampleAPI')
    def test_spec_title(self):
        get_url = '/openapi-schema.json'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION=f'Token {self.token}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('info', json_resp)
        self.assertIn('title', json_resp['info'])

        self.assertEqual(json_resp['info']['title'], 'SampleAPI')

    @override_settings(LICENSE='Test License msg')
    def test_spec_license(self):
        get_url = '/openapi-schema.json'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION=f'Token {self.token}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('info', json_resp)
        self.assertIn('license', json_resp['info'])
        self.assertIn('name', json_resp['info']['license'])

        self.assertEqual(
            json_resp['info']['license']['name'], 'Test License msg'
        )

    def test_spec_permissions(self):
        """
            Model Crud has minimum_level to admin
            SuperUser can access the endpoint /crud/ from the generated spec
            SimpleUser and AnonymousUser can't access the endpoint /crud/
        """

        crud_url = '/openapi-schema.json'

        resp = self.client.get(
            crud_url, HTTP_AUTHORIZATION=f'Token {self.token}'
        )  #: superuser
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('paths', json_resp)
        self.assertIn("/api/v1.1/crud/", json_resp['paths'])

        resp = self.client.get(crud_url)  #: anonymous user
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('paths', json_resp)
        self.assertNotIn("/api/v1.1/crud/", json_resp['paths'])

        resp = self.client.get(
            crud_url, HTTP_AUTHORIZATION=f'Token {self.simpletoken}'
        )  #: simpleuser (authenticated)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_resp = resp.json()
        self.assertIn('paths', json_resp)
        self.assertNotIn("/api/v1.1/crud/", json_resp['paths'])
