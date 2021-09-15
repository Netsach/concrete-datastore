import time
from copy import deepcopy
from rest_framework.test import APITestCase
from django.conf import settings
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings

COPIED_REST_FRAMEOWRK_SETTINGS = deepcopy(settings.REST_FRAMEWORK)
COPIED_REST_FRAMEOWRK_SETTINGS.update(
    {
        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ),
        'DEFAULT_THROTTLE_RATES': {'anon': '2/minute', 'user': '2/minute'},
    }
)


@override_settings(DEBUG=True)
class CRUDTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

    @override_settings(ENABLE_THROTTLING=True)
    @override_settings(ANONYMOUS_THROTTLING_RATE='2/s')
    @override_settings(USER_THROTTLING_RATE='1/s')
    def test_throttling_all_users(self):
        #: Since throttling is enabled, we have to wait 1 second
        #: before running this test
        time.sleep(1)
        login_url = '/api/v1.1/auth/login/'

        #: Anonymous requests
        #: First anonymous request -> 200
        resp = self.client.post(
            login_url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        url_projects = '/api/v1.1/project/'

        #: Second anonymous request -> 200
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)

        #: Third anonymous request exceeds throttling limit -> 429
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        #: Authenticated user requests
        #: First user request -> 200
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: Second user request exceeds throttling limit -> 429
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(ENABLE_THROTTLING=True)
    @override_settings(ENABLE_AUTHENTICATED_USER_THROTTLING=False)
    @override_settings(ANONYMOUS_THROTTLING_RATE='2/s')
    @override_settings(USER_THROTTLING_RATE='1/s')
    def test_throttling_anonymous_users(self):
        #: Since throttling is enabled, we have to wait 1 second
        #: before running this test
        time.sleep(1)
        login_url = '/api/v1.1/auth/login/'

        #: Anonymous requests
        #: First anonymous request -> 200
        resp = self.client.post(
            login_url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        url_projects = '/api/v1.1/project/'

        #: Second anonymous request -> 200
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)

        #: Third anonymous request exceeds throttling limit -> 429
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        #: Authenticated user requests
        #: First user request -> 200
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: Second user request -> 200 (throttling is disabled for authenticated users)
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(ENABLE_THROTTLING=True)
    @override_settings(ENABLE_ANONYMOUS_USER_THROTTLING=False)
    @override_settings(ANONYMOUS_THROTTLING_RATE='2/s')
    @override_settings(USER_THROTTLING_RATE='1/s')
    def test_throttling_authenticated_users(self):
        #: Since throttling is enabled, we have to wait 1 second
        #: before running this test
        time.sleep(1)
        login_url = '/api/v1.1/auth/login/'

        #: Anonymous requests
        #: First anonymous request -> 200
        resp = self.client.post(
            login_url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        url_projects = '/api/v1.1/project/'

        #: Second anonymous request -> 200
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)

        #: Thrid anonymous request -> 200 (throttling is disabled for authenticated users)
        resp = self.client.get(url_projects)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: Authenticated user requests
        #: First user request -> 200
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
