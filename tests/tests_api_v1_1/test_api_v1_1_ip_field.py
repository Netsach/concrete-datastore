# coding: utf-8
from mock import MagicMock
import uuid
from rest_framework.test import APITestCase
from collections import OrderedDict
from rest_framework import status
import pendulum

from concrete_datastore.api.v1.filters import (
    FilterSupportingOrBackend,
    FilterSupportingRangeBackend,
)
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    Skill,
    DefaultDivider,
    DIVIDER_MODEL,
    Category,
)
from django.test import override_settings
from concrete_datastore.api.v1.datetime import format_datetime


@override_settings(DEBUG=True)
class GenericIpAdressFieldTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

    def test_success_create_with_valid_ip(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project and ensure that request is valid(201)
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                # "date_creation": timezone.now(),
                "ip_address": "127.0.0.1",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        # Retrieve the project by filtering
        resp = self.client.get(
            f'{url_projects}?ip_address=127.0.0.1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.json()['objects_count'], 1)

    def test_failure_create_with_invalid_ip(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project with an invalid IP address
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                # "date_creation": timezone.now(),
                "ip_address": "This is the ip of my project",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertEqual(
            resp.json(),
            {
                'ip_address': [
                    'Enter a valid IPv4 address.',
                    'Enter a valid IPv4 or IPv6 address.',
                ]
            },
            msg=resp.content,
        )
        self.assertEqual(Project.objects.count(), 0)

    def test_failure_create_with_ipv6(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        #: Create with an ipv6 IP rather than an ipv4
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                # "date_creation": timezone.now(),
                "ip_address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertEqual(
            resp.json(),
            {'ip_address': ['Enter a valid IPv4 address.']},
            msg=resp.content,
        )
        self.assertEqual(Project.objects.count(), 0)
