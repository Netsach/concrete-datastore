# coding: utf-8
import re
import pendulum
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import User, UserConfirmation


class DateTimeLoggerMiddleware(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url_login = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url_login, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.token = resp.data['token']

    def test_datetime_logger_on_status_endpoint(self):
        url = '/status/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_headers = resp.headers
        self.assertIn('DateTime-Received', resp_headers)
        self.assertIn('DateTime-Sent', resp_headers)
        datetime_received = resp_headers['DateTime-Received']
        datetime_sent = resp_headers['DateTime-Sent']
        #: Check if the dates have the right format
        date_time_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        self.assertIsNotNone(re.match(date_time_regex, datetime_received))
        self.assertIsNotNone(re.match(date_time_regex, datetime_sent))
        datetime_received_instance = pendulum.parse(datetime_received)
        datetime_sent_instance = pendulum.parse(datetime_sent)
        self.assertTrue(datetime_received_instance <= datetime_sent_instance)

    def test_datetime_logger_on_rest_api_view(self):
        url = '/api/v1.1/group/'
        resp = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_headers = resp.headers
        self.assertIn('DateTime-Received', resp_headers)
        self.assertIn('DateTime-Sent', resp_headers)
        datetime_received = resp_headers['DateTime-Received']
        datetime_sent = resp_headers['DateTime-Sent']
        #: Check if the dates have the right format
        date_time_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        self.assertIsNotNone(re.match(date_time_regex, datetime_received))
        self.assertIsNotNone(re.match(date_time_regex, datetime_sent))
        datetime_received_instance = pendulum.parse(datetime_received)
        datetime_sent_instance = pendulum.parse(datetime_sent)
        self.assertTrue(datetime_received_instance <= datetime_sent_instance)
