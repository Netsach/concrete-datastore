# coding: utf-8
import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import authenticate

# from django.utils import timezone
from django.test import Client

# from uuid import uuid4
from concrete_datastore.concrete.models import User, UserConfirmation


from django.test import override_settings


@override_settings(DEBUG=True)
class AuthTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.admin, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "plop"}
        )
        self.token_admin = resp.data['token']
        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.manager, confirmed=True
        ).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "manager@netsach.org", "password": "plop"}
        )
        self.token_manager = resp.data['token']

    def test_get_blocked_user(self):
        blocked_user1 = User.objects.create(
            email='blocked1@netsach.org', is_active=False
        )
        blocked_user2 = User.objects.create(
            email='blocked2@netsach.org', is_active=False
        )
        self.assertEqual(User.objects.count(), 4)
        url_user = '/api/v1.1/user/'
        resp = self.client.get(
            url_user, HTTP_AUTHORIZATION=f'Token {self.token_admin}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.json())
        results = resp.json()['results']
        self.assertEqual(len(results), 2)
        result_uids = [user['uid'] for user in results]
        self.assertIn(str(self.admin.uid), result_uids)
        self.assertIn(str(self.manager.uid), result_uids)
        self.assertNotIn(str(blocked_user1.uid), result_uids)
        self.assertNotIn(str(blocked_user2.uid), result_uids)

        url_blocked_user = '/api/v1.1/blocked-users/'
        resp = self.client.get(
            url_blocked_user, HTTP_AUTHORIZATION=f'Token {self.token_manager}'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.get(
            url_blocked_user, HTTP_AUTHORIZATION=f'Token {self.token_admin}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.json())
        results = resp.json()['results']
        self.assertEqual(len(results), 2)
        result_uids = [user['uid'] for user in results]
        self.assertNotIn(str(self.admin.uid), result_uids)
        self.assertIn(str(blocked_user1.uid), result_uids)
        self.assertIn(str(blocked_user2.uid), result_uids)

    def test_unblock_user(self):
        unblock_url = '/api/v1.1/unblock-users'
        blocked_user1 = User.objects.create(
            email='blocked1@netsach.org', is_active=False
        )
        blocked_user2 = User.objects.create(
            email='blocked2@netsach.org', is_active=False
        )
        active_user = User.objects.create(email='active@netsach.org')
        resp = self.client.post(
            unblock_url,
            data={
                'user_uids': [
                    str(blocked_user1.uid),
                    str(blocked_user2.uid),
                    str(active_user.uid),
                ]
            },
            HTTP_AUTHORIZATION=f'Token {self.token_admin}',
        )
        data = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(str(blocked_user1.uid), data.keys())
        self.assertEqual(
            data[str(blocked_user1.uid)], 'User successfully unblocked'
        )
        self.assertIn(str(blocked_user2.uid), data.keys())
        self.assertEqual(
            data[str(blocked_user2.uid)], 'User successfully unblocked'
        )
        self.assertIn(str(active_user.uid), data.keys())
        self.assertEqual(data[str(active_user.uid)], 'User is already active')

    def test_unblock_user_wrong_uid(self):
        unblock_url = '/api/v1.1/unblock-users'
        resp = self.client.post(
            unblock_url,
            data={'user_uids': [str(uuid.uuid4())]},
            HTTP_AUTHORIZATION=f'Token {self.token_admin}',
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unblock_user_permission(self):
        blocked_user = User.objects.create(
            email='blocked@netsach.org', is_active=False
        )
        unblock_url = '/api/v1.1/unblock-users'
        resp = self.client.post(
            unblock_url,
            data={'user_uids': [str(blocked_user.uid)]},
            HTTP_AUTHORIZATION=f'Token {self.token_manager}',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
