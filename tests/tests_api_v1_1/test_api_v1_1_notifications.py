# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class UserNotificationsTestCase(APITestCase):
    def setUp(self):

        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.save()
        confirmation = UserConfirmation.objects.create(user=self.user1)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        # USER B
        self.user2 = User.objects.create_user('userb@netsach.org')
        self.user2.set_password('plop')
        self.user2.save()
        confirmation = UserConfirmation.objects.create(user=self.user2)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        # USER C
        self.user3 = User.objects.create_user('userc@netsach.org')
        self.user3.set_password('plop')
        self.user3.save()
        confirmation = UserConfirmation.objects.create(user=self.user3)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "userc@netsach.org", "password": "plop"}
        )
        self.token_c = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")
        self.cloisonY = DefaultDivider.objects.create(name="TEST2")

        # Super User
        self.superuser = User.objects.create_user('superuser@netsach.org')
        self.superuser.set_password('plop')
        self.superuser.is_superuser = True
        self.superuser.save()
        confirmation = UserConfirmation.objects.create(user=self.superuser)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "superuser@netsach.org", "password": "plop"}
        )
        self.token_su = resp.data['token']

        self.user1.defaultdividers.add(self.cloisonX)

        self.user2.defaultdividers.add(self.cloisonX)
        self.user2.defaultdividers.add(self.cloisonY)

        self.user3.defaultdividers.add(self.cloisonX)
        self.user3.defaultdividers.add(self.cloisonY)

    def test_notifications_unsub_1_scope(self):
        url_account = '/api/v1.1/account/me/'

        # Update User to unsub  its scope notif
        resp = self.client.patch(
            url_account,
            data={"unsubscribe_to": [str(self.cloisonX.uid)]},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        # Get User A account Me
        resp = self.client.get(
            url_account, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(len(resp.data['unsubscribe_to']), 1)
        self.assertEqual(resp.data['unsubscribe_to'][0], self.cloisonX.uid)
        user = User.objects.get(uid=self.user1.uid)
        self.assertEqual(str(user.uid), resp.data['uid'])
        self.assertEqual(user.unsubscribe_to.all().exists(), True)
        scope = DefaultDivider.objects.get(uid=str(self.cloisonX.uid))
        self.assertEqual(scope.unsubscribed_users.all().exists(), True)

    def test_notifications_unsub_1_of_2_scope(self):
        url_account = '/api/v1.1/account/me/'

        # Update User to unsub  its scope notif
        resp = self.client.patch(
            url_account,
            data={"unsubscribe_to": [str(self.cloisonX.uid)]},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        # Get User A account Me
        resp = self.client.get(
            url_account, HTTP_AUTHORIZATION='Token {}'.format(self.token_b)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(len(resp.data['unsubscribe_to']), 1)
        self.assertIn(self.cloisonX.uid, resp.data['unsubscribe_to'])
        user = User.objects.get(uid=self.user2.uid)
        self.assertEqual(str(user.uid), resp.data['uid'])
        self.assertEqual(user.unsubscribe_to.all().exists(), True)
        scope = DefaultDivider.objects.get(uid=str(self.cloisonX.uid))
        self.assertEqual(scope.unsubscribed_users.all().exists(), True)

    def test_notifications_unsub_all(self):
        url_account = '/api/v1.1/account/me/'

        # Update User to unsub  its scope notif
        resp = self.client.patch(
            url_account,
            data={"unsubscribe_all": True},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_c),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        # Get User C account Me
        resp = self.client.get(
            url_account, HTTP_AUTHORIZATION='Token {}'.format(self.token_c)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(resp.data['unsubscribe_all'], True)
        user = User.objects.get(uid=self.user3.uid)
        self.assertEqual(str(user.uid), resp.data['uid'])
        self.assertEqual(user.unsubscribe_all, True)

    def test_unsub_from_django_view_with_token(self):
        '''
        1. Superuser get a token related to one user
        2. An anonymous user use this token to access unsub view
        3. Unsub all
        '''
        url_account = '/api/v1.1/account/me/'
        user_detail_url = '/api/v1.1/user/{}/'.format(self.user1.uid)

        resp = self.client.get(
            user_detail_url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_su),
        )
        self.assertEqual(resp.status_code, 200)
        notification_url = resp.data['unsubscribe_notification_url'].split(
            'http://testserver:80'
        )[1]

        resp = self.client.get(notification_url)
        self.assertEqual(resp.status_code, 200)
        # Simulate form response
        resp = self.client.post(
            '/c/unsubscribe-notifications-result/{token}'.format(
                token=self.user1.subscription_notification_token
            ),
            data={'all': 1, 'scope': []},
        )
        self.assertEqual(resp.status_code, 200)

        # Get user account me and assert results
        resp = self.client.get(
            url_account, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertTrue(resp.data['unsubscribe_all'])
        self.assertEqual(resp.data['unsubscribe_to'], [])
