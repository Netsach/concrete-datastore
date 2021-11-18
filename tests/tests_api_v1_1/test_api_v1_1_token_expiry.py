# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    AuthToken,
)
from datetime import timedelta
import pendulum


@override_settings(DEBUG=True)
class AuthTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org',
            password='plop'
            # 'John',
            # 'Doe',
        )
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()

    # Set expiry to 3 days
    @override_settings(API_TOKEN_EXPIRY=3 * 60 * 24)
    def test_token_expiry(self):
        url = '/api/v1.1/auth/login/'
        url_projects = '/api/v1.1/project/'

        # Login to generate first token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token = resp.data['token']

        # Expired the previous generated token
        old_token = AuthToken.objects.first()
        old_token.expiration_date += timedelta(-10)
        old_token.save()

        # CREATE a project with the expired token
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(old_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 0)

        # Login again to generate a new token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token = resp.data['token']

        self.assertNotEqual(token, old_token.key)

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a project with the new token
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        # Try CREATE a project with old token
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects3",
                "description": "ExpiredToken",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(old_token.key),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        # Set expiry to 3 days

    @override_settings(
        API_TOKEN_EXPIRY=3 * 60 * 24,
        ALLOW_MULTIPLE_AUTH_TOKEN_SESSION=False,
        USE_MULTIPLE_TOKENS=True,
    )
    def test_token_expired_if_login_twice(self):

        url = '/api/v1.1/auth/login/'

        # Login to generate first token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        first_token = resp.data['token']

        # Login to generate second token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        second_token = resp.data['token']

        self.assertNotEqual(first_token, second_token)

    # Set expiry to 3 days
    @override_settings(
        API_TOKEN_EXPIRY=3 * 60 * 24,
        ALLOW_MULTIPLE_AUTH_TOKEN_SESSION=True,
        USE_MULTIPLE_TOKENS=True,
    )
    def test_same_token_not_expired_if_login_twice(self):

        url = '/api/v1.1/auth/login/'

        # Login to generate first token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        first_token = resp.data['token']

        # Login to generate second token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        second_token = resp.data['token']

        self.assertNotEqual(first_token, second_token)

    @override_settings(
        API_TOKEN_EXPIRY=3 * 60 * 24,
        ALLOW_MULTIPLE_AUTH_TOKEN_SESSION=True,
        USE_MULTIPLE_TOKENS=False,
    )
    def test_different_token_not_expired_if_login_twice(self):

        url = '/api/v1.1/auth/login/'

        # Login to generate first token

        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        first_token = resp.data['token']

        # Login to generate second token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        second_token = resp.data['token']

        self.assertEqual(first_token, second_token)

    @override_settings(
        API_TOKEN_EXPIRY=3 * 60 * 24, EXPIRY_EXTRA_PERIOD=2 * 60
    )
    def test_token_not_expired_if_spare_time(self):
        url = '/api/v1.1/auth/login/'
        url_projects = '/api/v1.1/project/'

        # Login to generate token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token_key = resp.data['token']

        now = pendulum.now('utc')
        one_hour_earlier = now.add(hours=-1)
        three_hours_earlier = now.add(hours=-3)

        # CREATE a project with the token, so his last action is now
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects1",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(token_key),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        # Update the token so it's expired since three hours but spare time
        # is not over

        AuthToken.objects.filter(key=token_key).update(
            expiration_date=three_hours_earlier,
            last_action_date=one_hour_earlier,
        )

        # CREATE another project with the expired token,
        # Spare time of 2 hours is not over so it should be created
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                "description": "description de mon projet 2",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(token_key),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 2)

        # Update the token so it's expired since three hours
        AuthToken.objects.filter(key=token_key).update(
            expiration_date=three_hours_earlier,
            last_action_date=three_hours_earlier,
        )

        # CREATE another project with the expired token,
        # Spare time of 2 hours is over it should NOT be created.
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects3",
                "description": "description de mon projet 3",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(token_key),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 2)

    def test_token_with_blocked_user(self):
        url = '/api/v1.1/auth/login/'
        url_projects = '/api/v1.1/project/'

        # Login to generate token
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token_key = resp.data['token']
        self.user.is_active = False
        self.user.save()

        # CREATE a project with the user blocked
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects1",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(token_key),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 0)
