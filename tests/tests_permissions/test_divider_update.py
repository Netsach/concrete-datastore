# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    DefaultDivider,
    UserConfirmation,
    Project,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class UnscopedRequestPermissionsTestCase(APITestCase):
    def create_custom_user(self, level, suffixe='', scopes=None):
        if scopes is None:
            scopes = []
        username = '{}_{}'.format(level, suffixe) if suffixe else level
        email = '{}@netsach.org'.format(username)

        user = User.objects.create_user(email)
        user.set_password('plop')
        user.set_level(level)

        for scope in scopes:
            user.defaultdividers.add(scope)
        user.save()

        confirmation = UserConfirmation.objects.create(user=user)
        confirmation.confirmed = True
        confirmation.save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(url, {"email": email, "password": "plop"})

        return user, resp.data['token']

    def setUp(self):

        self.scope_1 = DefaultDivider.objects.create(name="Scope 1")
        self.scope_2 = DefaultDivider.objects.create(name="Scope 2")

        self.manager, self.token_manager = self.create_custom_user(
            level='manager'
        )
        self.manager.defaultdividers.add(self.scope_2)

        self.project1 = Project.objects.create(
            name="project1", defaultdivider=self.scope_1, public=False
        )
        self.project1.can_admin_users.add(self.manager)

    def test_project(self):
        #:  update
        url = '/api/v1.1/project/'

        resp = self.client.patch(
            '{}{}/'.format(url, self.project1.uid),
            {"name": "Updated Name"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
            # HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
