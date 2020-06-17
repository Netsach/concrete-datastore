# coding: utf-8
from rest_framework.test import APITestCase
from django.test import override_settings
from rest_framework import status
from django.utils import timezone
from concrete_datastore.concrete.models import User, UserConfirmation


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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    @override_settings(TIME_ZONE='Europe/Paris', USE_TZ=True)
    def test_utc_bad_use(self):
        # Ensure timezone is still aware
        self.assertTrue(timezone.is_aware(timezone.now()))

        resp = self.client.post(
            "/api/v1.1/date-utc/",
            data={"datetime": "2018-05-07T12:44:29Z"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        url_create_date = resp.data['datetime']
        self.assertNotEqual(url_create_date, "2018-05-07T12:44:29Z")

    @override_settings(TIME_ZONE='UTC', USE_TZ=True)
    def test_utc_timezone_utc(self):
        # Ensure timezone is still aware
        self.assertTrue(timezone.is_aware(timezone.now()))

        resp = self.client.post(
            "/api/v1.1/date-utc/",
            data={"datetime": "2018-05-07T12:44:29Z"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        url_create_date = resp.data['datetime']
        self.assertEqual(url_create_date, "2018-05-07T12:44:29Z")

    @override_settings(TIME_ZONE='Europe/Paris', USE_TZ=False)
    def test_utc_tz_false(self):
        # Ensure timezone is still aware
        self.assertFalse(timezone.is_aware(timezone.now()))
        # Never use USE_TZ = False

    @override_settings(TIME_ZONE='UTC', USE_TZ=False)
    def test_utc_both(self):
        # Ensure timezone is still aware
        self.assertFalse(timezone.is_aware(timezone.now()))
        # Never use USE_TZ = False
