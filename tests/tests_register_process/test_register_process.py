# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_409_CONFLICT, HTTP_202_ACCEPTED

from concrete_datastore.concrete.models import User, AuthToken


class RegisterProcessTestCase(APITestCase):
    def setUp(self):
        self.token = '0aa70874-e1ad-4a11-87db-6c4bbea7b985'

    def test_register_process(self):
        url_register_process = '/api/v1.1/process/register/'
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(AuthToken.objects.count(), 0)

        resp = self.client.post(
            url_register_process,
            {
                'application': 'app1',
                'instance': 'instance2',
                'token': self.token,
            },
        )
        self.assertEqual(resp.status_code, HTTP_202_ACCEPTED, msg=resp.content)
        self.assertDictEqual(
            resp.json(),
            {
                'token': self.token,
                'msg': 'Process successfully registered',
                'level': 'Blocked',
            },
            msg=resp.content,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

        token_obj = AuthToken.objects.first()
        self.assertEqual(token_obj.key, self.token)
        self.assertEqual(token_obj.user.email, 'app1_instance2@netsach.com')
        self.assertEqual(token_obj.user.level, 'blocked')

    def test_register_process_already_registered(self):
        url_register_process = '/api/v1.1/process/register/'

        user = User.objects.create(email='app1_instance2@netsach.com')
        AuthToken.objects.create(key=self.token, user=user)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(AuthToken.objects.count(), 1)

        resp = self.client.post(
            url_register_process,
            {
                'application': 'app1',
                'instance': 'instance2',
                'token': self.token,
            },
        )
        self.assertEqual(resp.status_code, HTTP_202_ACCEPTED, msg=resp.content)
        self.assertDictEqual(
            resp.json(),
            {
                'token': self.token,
                'msg': 'Process successfully registered',
                'level': 'SimpleUser',
            },
            msg=resp.content,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

        token_obj = AuthToken.objects.first()
        self.assertEqual(token_obj.key, self.token)
        self.assertEqual(token_obj.user.email, 'app1_instance2@netsach.com')

    def test_register_process_user_existing_token(self):
        # If the process register with a non existing token but there is
        # an existing user with a token
        url_register_process = '/api/v1.1/process/register/'

        user = User.objects.create(email='app1_instance2@netsach.com')
        AuthToken.objects.create(key=self.token, user=user)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(AuthToken.objects.count(), 1)

        token2 = '2d5c6695-c7fd-44e8-b4f2-c21e0d320d6c'

        resp = self.client.post(
            url_register_process,
            {'application': 'app1', 'instance': 'instance2', 'token': token2},
        )
        self.assertEqual(resp.status_code, HTTP_409_CONFLICT, msg=resp.content)
        self.assertDictEqual(
            resp.json(),
            {'msg': 'Email address already used with a different token'},
            msg=resp.content,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

    def test_register_process_token_existing_user(self):
        # If the process register with an existing token but there is
        # another existing token with the user
        url_register_process = '/api/v1.1/process/register/'

        user = User.objects.create(email='app1_instance2@netsach.com')
        AuthToken.objects.create(key=self.token, user=user)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(AuthToken.objects.count(), 1)

        resp = self.client.post(
            url_register_process,
            {
                'application': 'app1',
                'instance': 'instanceDIFFERENT',
                'token': self.token,
            },
        )
        self.assertEqual(resp.status_code, HTTP_409_CONFLICT, msg=resp.content)
        self.assertDictEqual(
            resp.json(),
            {'msg': 'Email address already used with a different token'},
            msg=resp.content,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
