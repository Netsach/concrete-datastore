# coding: utf-8
import pendulum
import datetime
import time
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import override_settings
from concrete_datastore.concrete.models import User, UserConfirmation
from concrete_datastore.concrete.constants import MFA_OTP


class Timecop(object):
    """
    Class for freezing time. Ispired from
    https://github.com/pyauth/pyotp/blob/develop/test.py#L424
    """

    def __init__(self, freeze_timestamp):
        self.freeze_timestamp = freeze_timestamp

    def __enter__(self):
        self.real_datetime = datetime.datetime
        self.real_pendulum_now = pendulum.now
        self.real_timestamp_fn = time.time
        datetime.datetime = self.frozen_datetime()
        pendulum.now = self.frozen_now()
        time.time = self.frozen_timestamp()

    def __exit__(self, type, value, traceback):
        datetime.datetime = self.real_datetime
        pendulum.now = self.real_pendulum_now
        time.time = self.real_timestamp_fn

    def frozen_timestamp(self):
        def time():
            return self.freeze_timestamp

        return time

    def frozen_now(self):
        def now(*args, **kwargs):
            return pendulum.from_timestamp(self.freeze_timestamp, **kwargs)

        return now

    def frozen_datetime(self):
        class FrozenDateTime(datetime.datetime):
            @classmethod
            def now(cls, **kwargs):
                return cls.fromtimestamp(self.freeze_timestamp, **kwargs)

        return FrozenDateTime


@override_settings(USE_TWO_FACTOR_AUTH=True)
class AuthTestCase(APITestCase):
    def setUp(self):

        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        self.user.emaildevice_set.create(
            confirmed=True,
            mfa_mode=MFA_OTP,
            key='3132333435363738393031323334353637383930',
        )

    @override_settings(OTP_TOTP_TOLERANCE=0)
    def test_authentication_mfa(self):
        self.assertIsNotNone(self.user.totp_device)

        login_url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            login_url,
            data={'email': 'johndoe@netsach.org', 'password': 'plop'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_verified'])

        temporary_token = resp.data['token']

        with Timecop(0):
            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '755224',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data['is_verified'])

        resp = self.client.post(
            login_url,
            data={'email': 'johndoe@netsach.org', 'password': 'plop'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_verified'])

        temporary_token = resp.data['token']

        with Timecop(60):
            #: With tolerance to 0, only the current code is authorized.
            #: the code 287082 is for timestamp 30, so it has expired
            #: the code 359152 is the current code
            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '287082',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
            resp = self.client.post(
                login_url,
                data={'email': 'johndoe@netsach.org', 'password': 'plop'},
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertFalse(resp.data['is_verified'])

            temporary_token = resp.data['token']

            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '359152',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data['is_verified'])

    @override_settings(OTP_TOTP_TOLERANCE=1)
    def test_authentication_mfa_with_tolerance(self):
        self.assertIsNotNone(self.user.totp_device)

        login_url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            login_url,
            data={'email': 'johndoe@netsach.org', 'password': 'plop'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_verified'])

        temporary_token = resp.data['token']

        with Timecop(0):
            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '755224',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data['is_verified'])

        resp = self.client.post(
            login_url,
            data={'email': 'johndoe@netsach.org', 'password': 'plop'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_verified'])

        temporary_token = resp.data['token']

        with Timecop(60):
            #: With tolerance = 1, we autorize the current code (359152) as
            #: well as the previous code (287082)
            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '287082',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data['is_verified'])
            resp = self.client.post(
                login_url,
                data={'email': 'johndoe@netsach.org', 'password': 'plop'},
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertFalse(resp.data['is_verified'])

            temporary_token = resp.data['token']

            resp = self.client.post(
                '/api/v1.1/auth/two-factor/login/',
                data={
                    'email': 'johndoe@netsach.org',
                    'token': temporary_token,
                    'verification_code': '359152',
                },
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(resp.data['is_verified'])
