# coding: utf-8
import pendulum
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from django.test import Client
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings


@override_settings(DEBUG=True)
class AuthTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("usera@netsach.org")
        self.user.set_password("plop")
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = "/api/v1.1/auth/login/"
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token = resp.data["token"]

    def test_token_authentication_in_url(self):
        project_collections = "/api/v1.1/project/"
        client = Client()

        # Use without token to access the url_that_required_auth (401)
        resp = client.post(project_collections)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use token without settings headers
        project_collections = "/api/v1.1/project/?c_auth_with_token={}".format(
            self.token
        )
        resp = client.post(
            project_collections,
        )

        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED,
        )

        # Use invalid token
        project_collections = "/api/v1.1/project/?c_auth_with_token=xyz"
        resp = client.post(
            project_collections,
        )

        self.assertEqual(
            resp.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
