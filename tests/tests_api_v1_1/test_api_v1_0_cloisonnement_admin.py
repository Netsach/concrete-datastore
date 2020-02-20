# coding: utf-8
from rest_framework.test import APITestCase
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CloisonnementTestCase(APITestCase):
    def setUp(self):

        # USER ADMIN
        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.save()
        confirmation = UserConfirmation.objects.create(user=self.userA)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        # USER NON ADMIN
        self.userB = User.objects.create_user('userb@netsach.org')
        self.userB.set_password('plop')
        self.userB.save()
        confirmation = UserConfirmation.objects.create(user=self.userB)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.cloison1 = DefaultDivider.objects.create(name="TEST1")
        self.cloison2 = DefaultDivider.objects.create(name="TEST2")

        self.userA.defaultdividers.add(self.cloison1)
        self.userA.save()
        self.userB.defaultdividers.add(self.cloison2)
        self.userB.save()
