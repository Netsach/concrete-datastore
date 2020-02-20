# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
    DIVIDER_MODEL,
    UNDIVIDED_MODEL,
)
from django.apps import apps
from django.test import override_settings


@override_settings(DEBUG=True)
class CloisonnementMultipleTestCase(APITestCase):
    def setUp(self):

        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.save()
        confirmation = UserConfirmation.objects.create(user=self.userA)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        self.userB = User.objects.create_user('userb@netsach.org')
        self.userB.set_password('plop')
        self.userB.save()
        confirmation = UserConfirmation.objects.create(user=self.userB)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")
        self.cloisonY = DefaultDivider.objects.create(name="TEST2")
        self.userA.defaultdividers.add(self.cloisonX)
        self.userA.save()
        self.userB.defaultdividers.add(self.cloisonY)
        self.userB.save()

    def test_model_without_divider(self):
        fusee_model = apps.get_model("concrete.Fusee")
        village_model = apps.get_model("concrete.Village")
        divider_model = apps.get_model("concrete.{}".format(DIVIDER_MODEL))
        url_village = "/api/v1/village/"

        # divider_model._meta.get_all_related_objects()
        all_related_objects = [
            f
            for f in divider_model._meta.get_fields()
            if (f.one_to_many or f.one_to_one)
            and f.auto_created
            and not f.concrete
        ]

        for model in all_related_objects:
            # print(entity_model, model.related_model)
            self.assertNotEqual(fusee_model, model.related_model)
            self.assertNotEqual(village_model, model.related_model)

        self.assertIn('Village', UNDIVIDED_MODEL)
        self.assertIn('Fusee', UNDIVIDED_MODEL)

        # User A create a village (undivided)
        # Assert User A & B can access it
        resp = self.client.post(
            url_village,
            {"name": "Montalbert", "public": True},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        village = resp.data["url"]

        resp = self.client.get(
            village,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.get(
            village,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonY.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.get(
            village,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.get(
            village,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.patch(
            village,
            {"name": "Cabourg"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_b),
            HTTP_X_ENTITY_UID='{}'.format(self.cloisonY.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
