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
class CloisonnementMultipleTestCase(APITestCase):
    def setUp(self):

        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.save()
        confirmation = UserConfirmation.objects.create(user=self.user1)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1/auth/login/'
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
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")
        self.cloisonY = DefaultDivider.objects.create(name="TEST2")

        self.user1.defaultdividers.add(self.cloisonX)

        self.user2.defaultdividers.add(self.cloisonX)
        self.user2.defaultdividers.add(self.cloisonY)

        self.proj_a = Project.objects.create(
            name="projet A",
            description="tutu",
            defaultdivider=self.cloisonX,
            public=False,
        )
        self.proj_a.can_view_users.add(self.user1)

        self.proj_b = Project.objects.create(
            name="projet B",
            description="tutu",
            defaultdivider=self.cloisonY,
            public=False,
        )

        self.proj_c = Project.objects.create(
            name="projet C",
            description="tutu",
            defaultdivider=self.cloisonX,
            public=False,
        )
        self.proj_c.can_view_users.add(self.user1)

        self.proj_d = Project.objects.create(
            name="projet D",
            description="tutu",
            defaultdivider=self.cloisonX,
            public=False,
        )
        self.proj_d.can_view_users.add(self.user1)

        self.proj_e = Project.objects.create(
            name="projet E",
            description="tutu",
            defaultdivider=self.cloisonY,
            public=False,
        )

        self.assertEqual(Project.objects.count(), 5)

    # def test_cloisons_for_one_object(self):
    #     url_projects = '/api/v1/project/'

    #     # ASSERT USER A CAN ACCESS PROJ A
    #     self.assertIn(
    #         getattr(self.proj_a, DIVIDER_MODEL.lower()),
    #         self.user1.defaultdividers.all())
    #     resp = self.client.get(
    #         url_projects + '{}/'.format(self.proj_a.uid),
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
    #         **{'X-FRONT-UID':'{}'.format(self.cloisonX.uid)},
    #     )
    #     self.assertEqual(
    #         resp.status_code, status.HTTP_200_OK,
    #         msg=resp.content
    #     )

    #     # ASSERT USER A CANNOT ACCESS PROJ B
    #     self.assertNotIn(
    #         getattr(self.proj_b, DIVIDER_MODEL.lower()),
    #         self.user1.defaultdividers.all())
    #     resp = self.client.get(
    #         url_projects + str(self.proj_b.uid) + '/',
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
    #         **{'X-FRONT-UID':'{}'.format(self.cloisonY.uid)},
    #     )
    #     self.assertEqual(
    #         resp.status_code, status.HTTP_404_NOT_FOUND,
    #         msg=resp.content
    #     )

    #     # Assert USER B CAN ACCESS PROJ A
    #     self.assertIn(
    #         getattr(self.proj_a, DIVIDER_MODEL.lower()),
    #         self.user2.defaultdividers.all())
    #     resp = self.client.get(
    #         url_projects + '{}/'.format(self.proj_a.uid),
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token_b)
    #     )
    #     self.assertEqual(
    #         resp.status_code, status.HTTP_200_OK,
    #         msg=resp.content
    #     )

    #     # Assert USER B CAN ACCESS PROJ B
    #     self.assertIn(
    #         getattr(self.proj_b, DIVIDER_MODEL.lower()),
    #         self.user2.defaultdividers.all())
    #     resp = self.client.get(
    #         url_projects + '{}/'.format(self.proj_b.uid),
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token_b)
    #     )
    #     self.assertEqual(
    #         resp.status_code, status.HTTP_200_OK,
    #         msg=resp.content
    #     )

    def test_cloison_for_lists(self):
        url_project_list = '/api/v1/project/'

        # ASSERT USER A CAN only ACCESS PROJECTS WITH CLOISON X FROM FRONT X
        resp = self.client.get(
            url_project_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        # print(resp.data)
        self.assertEqual(resp.data["total_objects_count"], 3)

        # ASSERT USER A CANNOT ACCESS PROJECTS WITH CLOISON X FROM FRONT Y
        resp = self.client.get(
            url_project_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonY.uid),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK,
            # resp.data
        )
        self.assertEqual(resp.data["total_objects_count"], 0)

        url = Project.objects.get(name="projet B").uid
        resp = self.client.patch(
            '/api/v1/project/' + str(url) + '/',
            {"name": "pololo"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND,
            # resp.data
        )
        self.assertEqual(Project.objects.filter(name="pololo").count(), 0)

        # test no error 500
        resp = self.client.get(
            url_project_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(uuid.uuid4()),
        )
