# coding: utf-8
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
    def test_login_admin_view(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        resp = self.client.post(
            '/api/v1.1/auth/login/',
            {'email': 'johndoe@netsach.org', 'password': 'plop'},
        )
        self.token = resp.data['token']
        admin_url = (
            '/concrete-datastore-admin/login/?next=/concrete-datastore-admin/'
        )
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
