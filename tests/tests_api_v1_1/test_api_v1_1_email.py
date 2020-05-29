# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Email
from django.test import override_settings
import json


@override_settings(
    DEBUG=True,
    EMAIL_HOST='localhost',
    EMAIL_PORT=1025,
    EMAIL_HOST_USER='',
    EMAIL_HOST_PASSWORD='',
)
class EmailTest(APITestCase):
    def setUp(self):
        # User A
        self.userA = User.objects.create_user('aaaa@netsach.org')
        self.userA.set_password('userA')
        self.userA.save()
        confirmation = UserConfirmation.objects.create(
            user=self.userA, confirmed=True
        )
        confirmation.save()

        # User B
        self.userB = User.objects.create_user('bbbb@netsach.org')
        self.userB.set_password('userB')
        self.userB.save()
        confirmation = UserConfirmation.objects.create(
            user=self.userB, confirmed=True
        )
        confirmation.save()

    def test_send_email(self):
        self.assertEqual(User.objects.count(), 2)
        url_login = '/api/v1.1/auth/login/'
        url_email = '/api/v1.1/email/'
        # Login User A and user B
        resp = self.client.post(
            url_login, {"email": "aaaa@netsach.org", "password": "userA"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.token_user_A = resp.data['token']
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Send message to 2 users.
        resp = self.client.post(
            url_email,
            {
                "subject": "email de test",
                "body": "coucou, comment vas-tu?",
                "receiver_uid": self.userB.uid,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertIn('resource_status', resp.data)
        self.assertEqual(resp.data['resource_status'], 'sent')

        self.assertIn('uid', resp.data)
        instance_mail = Email.objects.get(uid=resp.data['uid'])
        self.assertEqual(instance_mail.receiver.uid, self.userB.uid)

    def test_send_email_on_error(self):
        url_login = '/api/v1.1/auth/login/'
        url_email = '/api/v1.1/email/'

        # Send message without auth
        resp = self.client.post(
            url_email,
            json.dumps(
                {
                    "subject": "email de test",
                    "body": "coucou, comment vas-tu?",
                    "receiver_uid": None,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.data
        )

        # Login User A
        resp = self.client.post(
            url_login, {"email": "aaaa@netsach.org", "password": "userA"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.token_user_A = resp.data['token']

        # send email with invalid receiver

        resp = self.client.post(
            url_email,
            {
                "subject": "email de test",
                "body": "coucou, comment vas-tu?",
                "receiver": "friend",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # send email without body
        resp = self.client.post(
            url_email,
            {
                "subject": "email de test",
                # "body": "coucou, comment vas-tu?",
                "receiver_uid": self.userB.uid,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual('send-error', resp.data['resource_status'])
        self.assertEqual(
            'Some fields are empty', resp.data['resource_message']
        )
