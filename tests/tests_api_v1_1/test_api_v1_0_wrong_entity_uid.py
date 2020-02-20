# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    DefaultDivider,
)
import uuid
from django.test import override_settings


@override_settings(DEBUG=True)
class CloisonnementTestCase(APITestCase):
    def setUp(self):

        # USER ADMIN
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.cloison = DefaultDivider.objects.create(name="TEST1")

        self.user.defaultdividers.add(self.cloison)
        self.user.save()

        self.proj_a = Project.objects.create(
            name="projet A",
            description="tutu",
            defaultdivider=self.cloison,
            public=False,
            additional_filtering=True,
        )
        self.proj_a.can_view_users.add(self.user)

    def test_retrieve_model_with_wrong_entity_uid(self):
        url_projects = '/api/v1.1/project/'
        wrong_entity_uid = uuid.uuid4()
        self.assertEqual(Project.objects.count(), 1)

        resp = self.client.get(
            url_projects,
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=wrong_entity_uid,
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 0)

    def test_retrieve_object_with_wrong_entity_uid(self):
        url_projects = '/api/v1.1/project/'
        wrong_entity_uid = uuid.uuid4()
        self.assertEqual(Project.objects.count(), 1)

        resp = self.client.get(
            url_projects + '{}/'.format(self.proj_a.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=wrong_entity_uid,
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.json(), {"detail": "Not found."})
