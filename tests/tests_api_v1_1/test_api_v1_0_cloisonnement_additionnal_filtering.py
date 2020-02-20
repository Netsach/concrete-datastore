# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    DefaultDivider,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class AdditionalFilteringTestCase(APITestCase):
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

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")

        self.user1.defaultdividers.add(self.cloisonX)
        self.user1.save()
        self.user2.defaultdividers.add(self.cloisonX)
        self.user2.save()

        self.proj_a = Project.objects.create(
            name="projet A",
            description="tutu",
            defaultdivider=self.cloisonX,
            public=False,
            additional_filtering=True,
        )
        self.proj_a.can_view_users.add(self.user1)

    def test_additional_filtering(self):
        url_projects = 'http://127.0.0.1:7777/api/v1.1/project/'

        # ASSERT USER 1 CAN ACCESS PROJ A
        resp = self.client.get(
            url_projects + '{}/'.format(self.proj_a.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            headers={'FRONT_UID': '{}'.format(self.cloisonX.uid)},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        # ASSERT USER 2 CANNOT ACCESS PROJ A

        resp = self.client.get(
            url_projects + '{}/'.format(self.proj_a.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_404_NOT_FOUND, msg=resp.content
        )
