# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    DefaultDivider,
    Fusee,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CreationCloisonnementTestCase(APITestCase):
    def setUp(self):

        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.is_staff = True
        self.user1.save()
        UserConfirmation.objects.create(user=self.user1, confirmed=True).save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        # USER B
        self.user2 = User.objects.create_user('userb@netsach.org')
        self.user2.set_password('plop')
        self.user2.save()
        UserConfirmation.objects.create(user=self.user2, confirmed=True).save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")

        self.user1.defaultdividers.add(self.cloisonX)
        self.user1.save()
        self.user2.defaultdividers.add(self.cloisonX)
        self.user2.save()

        # self.proj_a = Project.objects.create(
        #     name="projet A",
        #     description="tutu",
        #     defaultdivider=self.cloisonX,
        #     public=False,
        #     additional_filtering=True,
        # )
        # self.proj_a.can_view_users.add(self.user1)

    def test_scopes_allowed(self):
        url_projects = 'http://127.0.0.1:7777/api/v1/project/'

        # ASSERT USER 1 CAN ACCESS PROJ A
        resp = self.client.post(
            url_projects,
            data={
                'name': "projet A",
                'description': "tutu",
                'public': False,
                'additional_filtering': True,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        created_project = Project.objects.first()

        self.assertIsNotNone(created_project.defaultdivider)
        self.assertEqual(created_project.defaultdivider.uid, self.cloisonX.uid)

        rsp = self.client.get(
            url_projects,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        result = rsp.data.get('results')

        scopes = result[0].get('scopes')

        self.assertNotEqual(scopes, None)

    def test_scopes_allowed_simpleuser(self):
        url_projects = 'http://127.0.0.1:7777/api/v1/project/'

        # ASSERT USER 1 CAN ACCESS PROJ A
        resp = self.client.post(
            url_projects,
            data={
                'name': "projet A",
                'description': "tutu",
                'public': False,
                'additional_filtering': True,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        created_project = Project.objects.first()

        self.assertIsNotNone(created_project.defaultdivider)
        self.assertEqual(created_project.defaultdivider.uid, self.cloisonX.uid)

        rsp = self.client.get(
            url_projects,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        result = rsp.data.get('results')

        scopes = result[0].get('scopes')

        self.assertDictEqual(scopes, {"entity_uid": self.cloisonX.uid})

    def test_scopes_undivided_model(self):
        # Model Fusee is not divided

        url_fusees = 'http://127.0.0.1:7777/api/v1/fusee/'

        resp = self.client.post(
            url_fusees,
            data={'name': "Fusée A"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Fusee.objects.count(), 1)

        rsp = self.client.get(
            url_fusees,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        result = rsp.data.get('results')

        scopes = result[0].get('scopes')

        # Fusee is not divided, so scopes must be None, even with privileged users
        self.assertEqual(scopes, None)
